import logging
import datetime
from flask import Request, Response, escape, make_response
from google.cloud import tasks_v2

tasks_client = tasks_v2.CloudTasksClient()
from google.protobuf import duration_pb2, timestamp_pb2

import json
import re

import config
from utils.bq import bq_load_json_list, format_list_of_dicts_for_bq, get_schema_from_json_list
from pd_utils import logging_utils, monitoring_utils
from services.amz_advertising.amz_advertising import AmazonAdvertisingApiService


logging_utils.set_up_logging()

if config.SERVICE_INSTANCE in ["prod"]:
    monitoring_utils.init_rollbar_gcf(
        service=config.SERVICE_NAME, service_instance=config.SERVICE_INSTANCE, token=config.ROLLBAR_TOKEN
    )

ACCOUNTS = [
    {"country_code": "IT", "region": "EU", "account_id": "A2XUCHH4V8K2G7"},
    {"country_code": "ES", "region": "EU", "account_id": "A2XUCHH4V8K2G7"},
    {"country_code": "UK", "region": "EU", "account_id": "A2XUCHH4V8K2G7"},
    {"country_code": "DE", "region": "EU", "account_id": "A2XUCHH4V8K2G7"},
    {"country_code": "FR", "region": "EU", "account_id": "A2XUCHH4V8K2G7"},
    {"country_code": "JP", "region": "FE", "account_id": "A7GIQA99KT3M2"},
    {"country_code": "AU", "region": "FE", "account_id": "A1IL7L9R0WHXJX"},
    {"country_code": "MX", "region": "NA", "account_id": "A2F1M85EMKLCHV"},
    {"country_code": "CA", "region": "NA", "account_id": "A2F1M85EMKLCHV"},
    {"country_code": "US", "region": "NA", "account_id": "A2F1M85EMKLCHV"},
]

REPORT_COMBINATIONS = {
    "hsa": ["campaigns"],
    "sp": ["campaigns", "productAds", "targets"],
    "sd": ["campaigns", "productAds", "targets"],
}

# Possible REPORT_COMBINATONS
# "hsa": ["campaigns", "adGroups", "keywords"],
# "sp": ["campaigns", "adGroups", "keywords", "productAds", "asins", "targets"],
# 'sd': ['campaigns', 'adGroups', 'productAds', 'asins', 'targets']


def main(request: Request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <http://flask.pocoo.org/docs/1.0/api/#flask.Request>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>.
    """

    logging.info(
        "{}.{}.{}.{} invoked with {}".format(
            config.GCP_PROJECT, config.SERVICE_NAME, config.SERVICE_VERSION, config.SERVICE_INSTANCE, request.method
        )
    )

    try:
        # Up message if GET request
        if request.method == "GET":
            up_msg = "Service is up: {}.{}.{}.{}".format(
                config.GCP_PROJECT, config.SERVICE_NAME, config.SERVICE_INSTANCE, config.SERVICE_INSTANCE
            )
            logging.info(up_msg)

            args = request.args

            target_project = args.get("target_project")
            target_dataset = args.get("target_dataset")
            backfill_days = int(args.get("backfill_days"))

            report_counter = 0
            dates = []
            today = datetime.date.today()
            tasks_client = tasks_v2.CloudTasksClient()
            tasks_parent = tasks_client.queue_path("precis-aarhus-internal", "europe-west1", "lastobject-amz-api-queue")

            now_str = datetime.datetime.now().strftime("%m/%d/%Y-%H:%M:%S")

            for i in range(1, backfill_days + 1):
                dates.append((today - datetime.timedelta(days=i)).strftime("%Y%m%d"))

            for account in ACCOUNTS:
                amz_api_service = AmazonAdvertisingApiService(region=account["region"])
                for ad_type, record_types in REPORT_COMBINATIONS.items():
                    for record_type in record_types:
                        if ad_type == "sd":
                            list_to_iterate_over = ["T00030", "remarketing"]
                        elif ad_type == "hsa":
                            list_to_iterate_over = [None, "video"]
                        else:
                            list_to_iterate_over = [None]

                        for element in list_to_iterate_over:
                            for report_date in dates:
                                logging.info(
                                    f"Initiating report for: target_dataset:{target_dataset}, target_project:{target_project}, country_code:{account['country_code']}, region:{account['region']}, ad_type:{ad_type}, record_type:{record_type}, report_date:{report_date}"
                                )
                                tactic = element if ad_type == "sd" else None
                                creativeType = element if ad_type == "hsa" else None

                                try:
                                    report_id = amz_api_service.create_new_report(
                                        ad_type,
                                        record_type,
                                        report_date,
                                        account["country_code"],
                                        account["account_id"],
                                        tactic,
                                        creativeType,
                                    )
                                except Exception as e:
                                    logging.exception(e)
                                    logging.exception(
                                        f"{ad_type=},{record_type=},{report_date=},{account=},{tactic=},{creativeType=},"
                                    )
                                    report_id = None
                                if report_id == None:
                                    continue

                                task_config = {
                                    "target_dataset": target_dataset,
                                    "target_project": target_project,
                                    "specific_request": {
                                        "country_code": account["country_code"],
                                        "region": account["region"],
                                        "account_id": account["account_id"],
                                        "ad_type": ad_type,
                                        "record_type": record_type,
                                        "reportDate": report_date,
                                        "report_id": report_id,
                                        "tactic": element if ad_type == "sd" else None,
                                        "creativeType": element if ad_type == "hsa" else None,
                                    },
                                }

                                dispatch_standard_task(
                                    tasks_parent,
                                    tasks_v2.HttpMethod.GET,
                                    "https://europe-west1-precis-aarhus-internal.cloudfunctions.net/amz-advertising-api-lastobject",
                                    "amz-advertising-api-lastobject@precis-aarhus-internal.iam.gserviceaccount.com",
                                    tasks_parent
                                    + f"/tasks/"
                                    + re.sub(
                                        r"[^0-9a-zA-Z]+",
                                        "-",
                                        f"adhoc_amz_ads_{ad_type}_{record_type}_{tactic}_{creativeType}_{account['account_id']}_{account['country_code']}${report_date}_{now_str}",
                                    ),
                                    1800,
                                    task_config,
                                    delay=1800,
                                )

                                """
                                report_dict = amz_api_service.get_report(report_id,ad_type,record_type,report_date,account['country_code'],account['account_id'],tactic,creativeType)

                                report_to_upload_with_dates = []
                                reformatted_date = report_date[0:4]+"-"+report_date[4:6]+"-"+report_date[6:8]
                                for row in report_dict['report']:
                                    row['date'] = reformatted_date
                                    report_to_upload_with_dates.append(row)

                                reformatted_report = format_list_of_dicts_for_bq(report_to_upload_with_dates)

                                table_name = f"amz_ads_{ad_type}_{record_type}_{account['account_id']}_{account['country_code']}"

                                logging.info(f"Uploading report with the name: '{table_name}' for date: '{report_date}' to '{target_project}.{target_dataset}'")
                                bq_load_json_list(target_project, target_dataset, table_name, reformatted_report,report_date,report_dict['bq_schema'])
                                """
                                
                                report_counter += 1

            msg = f"Dispatched {report_counter} report tasks in total to '{target_project}.{target_dataset}'"
            logging.info(msg)
            return make_response(msg, 200)

        elif request.method == "POST":

            # Else parse args and echo name from URL args
            request_json = request.get_json()
            target_dataset = request_json.get("target_dataset")
            target_project = request_json.get("target_project")
            specific_request_metrics = request_json.get("specific_request")

            country_code = specific_request_metrics["country_code"]
            region = specific_request_metrics["region"]
            account_id = specific_request_metrics["account_id"]
            ad_type = specific_request_metrics["ad_type"]
            record_type = specific_request_metrics["record_type"]
            report_date = specific_request_metrics["reportDate"]
            tactic = specific_request_metrics["tactic"]
            creativeType = specific_request_metrics["creativeType"]

            report_id = specific_request_metrics.get("report_id")

            amz_api_service = AmazonAdvertisingApiService(region=region)
            if report_id == None:
                report_id = amz_api_service.create_new_report(
                    ad_type, record_type, report_date, country_code, account_id, tactic, creativeType
                )

            logging.info(
                f"Fetching report for: target_dataset:{target_dataset}, target_project:{target_project}, country_code:{country_code}, region:{region}, ad_type:{ad_type}, record_type:{record_type}, report_date:{report_date}"
            )

            report_dict = amz_api_service.get_report(
                report_id, ad_type, record_type, report_date, country_code, account_id, tactic, creativeType
            )
            if report_dict is None:
                return ""

            report_to_upload_with_dates = []
            for row in report_dict["report"]:
                row["date"] = f"{report_date[0:4]}-{report_date[4:6]}-{report_date[6:8]}"
                report_to_upload_with_dates.append(row)

            reformatted_report = format_list_of_dicts_for_bq(report_to_upload_with_dates)

            if tactic is not None:
                table_name = f"amz_ads_{ad_type}_{record_type}_{account_id}_{country_code}_{tactic}"
            elif creativeType is not None:
                table_name = f"amz_ads_{ad_type}_{record_type}_{account_id}_{country_code}_{creativeType}"
            else:
                table_name = f"amz_ads_{ad_type}_{record_type}_{account_id}_{country_code}"

            bq_load_json_list(
                target_project, target_dataset, table_name, reformatted_report, report_date, report_dict["bq_schema"]
            )

            msg = f"Uploaded 1 report with the name: '{table_name}' for date: '{report_date}' to '{target_project}.{target_dataset}'"
            logging.info(msg)

        return make_response(msg, 200)
    except Exception as e:
        logging.exception(e)
        msg = f"An error occured: {str(e)}"
        logging.error(msg)
        return make_response(msg, 500)


def dispatch_standard_task(
    tasks_parent, http_method, url, service_account, name, dispatch_deadline, task_config, delay=None
):
    dispatch_deadline_duration = duration_pb2.Duration()
    dispatch_deadline_duration.seconds = dispatch_deadline

    task = {
        "http_request": {  # Specify the type of request.
            "http_method": tasks_v2.HttpMethod.POST,
            "url": url,
            "headers": {"Content-Type": "application/json"},
            "oidc_token": {"service_account_email": service_account},
            "body": json.dumps(task_config).encode(),
        },
        "name": name,
        "dispatch_deadline": dispatch_deadline_duration,
    }

    if delay is not None:
        delayed_time = datetime.datetime.now() + datetime.timedelta(seconds=delay)
        delayed_timestamp = timestamp_pb2.Timestamp().FromDatetime(delayed_time)
        task["schedule_time"] = delayed_timestamp

    try:
        response = tasks_client.create_task(parent=tasks_parent, task=task)
        logging.info(f"Created task {response.name}")
    except Exception as e:
        msg = f"Error while creating task: {name} - {str(e)}"
        logging.exception(msg)
        raise Exception(msg)
