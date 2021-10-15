import requests
import logging

logging.basicConfig(level="INFO")
from datetime import datetime
import json
import os
import copy
import time
from gzip import decompress
import io
import csv

# Load this from Secrets Manager instead when deployed
from google.cloud import secretmanager
from pd_utils.service_to_service.service_account import ServiceAccountCredentials

secretmanager_client = secretmanager.SecretManagerServiceClient(credentials=ServiceAccountCredentials().get_credentials())
andreas_amz_credentials = json.loads(
secretmanager_client.access_secret_version(
        name="projects/269322900495/secrets/lo-az-ads/versions/1"
    ).payload.data.decode("UTF-8")
)

class AmazonAdvertisingApiService:
    def __init__(self, region, credentials=andreas_amz_credentials):
        if "refresh_token" not in credentials:
            raise Exception("Malformed Credentials - 'refresh_token' not found in the credentials.")

        self._credentials = credentials
        self._headers = {
            "Amazon-Advertising-API-ClientId": credentials["client_id"],
            "Content-Type": "application/json",
        }

        self._profiles = []

        self._pre_request_sleep_time = 0
        if region == "EU":
            self._base_url = "https://advertising-api-eu.amazon.com/v2"
        elif region == "NA":
            self._base_url = "https://advertising-api.amazon.com/v2"
        elif region == "FE":
            self._base_url = "https://advertising-api-fe.amazon.com/v2"

        self._auth_url = "https://api.amazon.com/auth/o2/token"

        with open("./services/amz_advertising/reports_fields.json") as reports_fields_file:
            self._reports_fields = json.load(reports_fields_file)

        with open("./services/amz_advertising/reports_fields_bq_schema.json") as reports_fields_bq_schema_file:
            self._reports_fields_bq_schema = json.load(reports_fields_bq_schema_file)

        self._refresh_access_token()

    def _make_request(self, url, method, headers=None, json_body=None, params=None, attempt=1):
        initial_pre_request_sleep_time = 0
        while initial_pre_request_sleep_time != self._pre_request_sleep_time:
            initial_pre_request_sleep_time = self._pre_request_sleep_time
            if initial_pre_request_sleep_time != 0:
                logging.info(f"Sleeping for {initial_pre_request_sleep_time} second before making request to: {url}")
                time.sleep(initial_pre_request_sleep_time)

        if method == "POST":
            res = requests.post(url, headers=headers, json=json_body, params=params)
        elif method == "GET":
            res = requests.get(url, headers=headers, params=params)

        if res.status_code == 200:
            self._pre_request_sleep_time = 0
            return res
        elif res.status_code == 202:
            self._pre_request_sleep_time = 0
            return res
        elif res.status_code == 404:
            raise Exception(
                f"Requested ressource not found at URL: {url} with parameters: {params} and json_body: {json_body}"
            )
        elif res.status_code == 429 or "Retry-After" in res.headers:
            self._pre_request_sleep_time = max(10 ** attempt * 2, self._pre_request_sleep_time)

            logging.info(f"Rate Limit hit. Attempt:{attempt}.")

            attempt = attempt + 1
            if attempt > 10:
                raise Exception(f"Attempts exceeded 10. API {res.status_code} Error:\n{res.text}")
            return self._make_request(url, method, headers, json_body, params, attempt)
        else:
            raise Exception(f"Unhandled API {res.status_code} Error:\n{res.text}")

    def _refresh_access_token(self):
        res = self._make_request(
            url=self._auth_url,
            method="POST",
            headers=self._headers,
            json_body={
                "grant_type": "refresh_token",
                "refresh_token": self._credentials["refresh_token"],
                "client_id": self._credentials["client_id"],
                "client_secret": self._credentials["client_secret"],
            },
        )

        access_token = res.json()["access_token"]

        self._headers["Authorization"] = f"Bearer {access_token}"
        return f"Bearer {access_token}"

    def _download_report(self, link, headers):
        report_res = self._make_request(url=link, method="GET", headers=headers)

        decompressed_file = decompress(report_res.content)
        return json.loads(decompressed_file)

    def list_profiles(self):
        if self._profiles == []:
            res = self._make_request(url=f"{self._base_url}/profiles", method="GET", headers=self._headers)

            self._profiles = res.json()

        return self._profiles

    def get_profile_id(self, country_code, account_id):
        all_profiles = self.list_profiles()

        for profile in all_profiles:
            if profile.get("countryCode") == country_code and profile.get("accountInfo").get("id") == account_id:
                return profile.get("profileId")

        raise Exception(f"Couldn't find profile with country_code '{country_code}' & account_id '{account_id}'")

    def get_report(self, report_id, ad_type, record_type, report_date, country_code, account_id, tactic, creativeType):
        profile_id = self.get_profile_id(country_code, account_id)

        headers = copy.deepcopy(self._headers)
        headers["Amazon-Advertising-API-Scope"] = str(profile_id)

        report_status = "IN_PROGRESS"

        while report_status == "IN_PROGRESS":
            time.sleep(5)
            report_fetch_res = self._make_request(
                url=f"{self._base_url}/reports/{report_id}", method="GET", headers=headers
            )

            report_fetch_json = report_fetch_res.json()

            report_status = report_fetch_json.get("status")

        if report_status != "SUCCESS":
            logging.warning(f"Generating report did not succeed: {report_fetch_res.text}")
            return None

        report = self._download_report(report_fetch_json["location"], headers)

        if tactic is not None:
            bq_schema = self._reports_fields_bq_schema[ad_type][record_type][tactic]
        else:
            bq_schema = self._reports_fields_bq_schema[ad_type][record_type]

        return {"report": report, "bq_schema": bq_schema}

    def create_new_report(
        self, ad_type, record_type, report_date, country_code, account_id, tactic=None, creativeType=None
    ):
        if record_type not in ["campaigns", "adGroups", "keywords", "productAds", "asins", "targets"]:
            raise Exception("Invalid value: record_type")

        if ad_type not in ["sp", "hsa", "sd"]:
            raise Exception("Invalid value: ad_type")

        profile_id = self.get_profile_id(country_code, account_id)

        headers = copy.deepcopy(self._headers)
        headers["Amazon-Advertising-API-Scope"] = str(profile_id)

        json_body = {}
        if ad_type == "hsa" and creativeType != None:
            json_body["creativeType"] = creativeType

        if record_type == "asins" and tactic is None:
            json_body["campaignType"] = "sponsoredProducts"

        if record_type == "campaigns" and tactic is None:
            json_body["segment"] = "placement"

        if record_type == "keywords" and tactic is None:
            json_body["segment"] = "query"

        if tactic is not None:
            if tactic == "remarketing" and country_code != "US":
                return None

            if tactic == "T00030" and country_code not in ["US", "CA", "UK", "DE", "FR", "IT", "ES", "AE", "JP", "IN"]:
                return None

            json_body["metrics"] = ",".join(self._reports_fields[ad_type][record_type][tactic])
            if self._reports_fields[ad_type][record_type][tactic] == []:
                return None
        elif ad_type == "hsa":
            key = creativeType if creativeType != None else "none"
            json_body["metrics"] = ",".join(self._reports_fields[ad_type][key][record_type])
        else:
            json_body["metrics"] = ",".join(self._reports_fields[ad_type][record_type])

        json_body["reportDate"] = report_date

        if tactic is not None:
            json_body["tactic"] = tactic

        report_init_res = self._make_request(
            url=f"{self._base_url}/{ad_type}/{record_type}/report", method="POST", headers=headers, json_body=json_body
        )

        return report_init_res.json().get("reportId")

        # return self.get_report(report_id,ad_type,record_type,report_date,country_code,account_id,tactic)


if __name__ == "__main__":
    amz_api_service = AmazonAdvertisingApiService(region="NA")
    # report_id = amz_api_service.create_new_report(
    #    "sd", "targets", "20210626", "US", "A2F1M85EMKLCHV", "remarketing", None
    # )
    # report = amz_api_service.get_report(
    #    report_id, "sd", "targets", "20210626", "US", "A2F1M85EMKLCHV", "remarketing", None
    # )
    # print(list(report["report"][0].keys()))
    #print(amz_api_service.list_profiles())
    # print(amz_api_service.create_new_report('sp','campaigns','20210407','US','A2F1M85EMKLCHV'))

    '''
    ## Jhonys Code
    access_token = amz_api_service._headers['Authorization']
    from requests.structures import CaseInsensitiveDict
    import pandas as pd
    def get_profiles(endpoint, access_token):
        url = endpoint + "/profiles"

        headers = CaseInsensitiveDict()
        headers['Content-Type'] = "application/json"
        headers['Authorization'] = access_token
        headers['Amazon-Advertising-API-ClientId'] = "amzn1.application-oa2-client.6581aec8607e470daa7f4a465f5c6bba"
        #headers['Amazon-Advertising-API-ClientId'] = amz_api_service._headers['Amazon-Advertising-API-ClientId']

        resp = requests.get(url, headers=headers)
        jsonfile=json.loads(resp.text)
        df = pd.DataFrame.from_dict(jsonfile, orient = 'columns')
        df['ingestion_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return df
    
    fe_endpoint = "https://advertising-api.amazon.com/v2"
    print(get_profiles(fe_endpoint,access_token))
    '''    

