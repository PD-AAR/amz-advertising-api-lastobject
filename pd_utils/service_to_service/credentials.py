import json
import logging

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

import config
from pd_utils.service_to_service import cache, iap


def load_user_credentials_from_info(credentials_json: dict, attempt_token_refresh=True) -> Credentials:
    credentials = Credentials(
        token=credentials_json.get("access_token", credentials_json.get("token")),
        refresh_token=credentials_json.get("refresh_token"),
        id_token=credentials_json.get("id_token"),
        token_uri=credentials_json.get("token_uri"),
        client_id=credentials_json.get("client_id"),
        client_secret=credentials_json.get("client_secret"),
        scopes=credentials_json.get("scopes"),
    )
    if not attempt_token_refresh:
        return credentials

    if credentials and not credentials.valid:
        request = Request()
        try:
            print("Refreshing Credentials")
            credentials.refresh(request)
        except RefreshError as e:
            raise e
            # Credentials could be expired or revoked. Try to reauthorize.
    return credentials


def get_credentials(auth_account: str) -> Credentials:
    cache_key = "auth::{}".format(auth_account)
    cache_value = cache.get(cache_key)
    if cache_value is None:

        assert "@precisdigital.com" in auth_account, "should be a precis digital email account"

        route = "/api/credentials?auth_account={}".format(auth_account)
        url = "{}{}".format(config.GAE_SERVICE_PRECIS_CENTRAL, route)
        logging.info("Fetching Credentials for {}; {}".format(auth_account, url))
        resp = iap.make_iap_request(url=url, client_id=config.GAE_SERVICE_PRECIS_CENTRAL_CLIENT_ID)
        cache_value = resp.json()
        cache.set(cache_key, cache_value)
    return load_user_credentials_from_info(cache_value)


def get_google_oauth_credentials(auth_account: str) -> Credentials:
    """
    An alias for get_credentials, with a more explicit name
    """
    return get_credentials(auth_account)


def credentials_to_dict(credenitals: Credentials) -> dict:

    out = json.loads(credenitals.to_json())
    # this object returns the access_token in the "token" field, so this corrects for that implementation
    if out.get("access_token") is None:
        out["access_token"] = out["token"]
    return out


def get_access_token(auth_account: str, service: str) -> dict:
    cache_key = f"auth::{service}::{auth_account}"
    cache_value = cache.get(cache_key)
    if cache_value is None:
        route = f"/api/access_token/{service}?auth_account={auth_account}"
        url = f"{config.GAE_SERVICE_PRECIS_CENTRAL}{route}"
        logging.info(f"Fetching Credentials for {auth_account} {service} {url}")
        resp = iap.make_iap_request(url=url, client_id=config.GAE_SERVICE_PRECIS_CENTRAL_CLIENT_ID)
        cache_value = resp.json()
        cache.set(cache_key, cache_value)
    return cache_value
