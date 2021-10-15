import logging
import os
from typing import List, Optional

import google.auth
import requests
from google.auth import impersonated_credentials
from google.auth.transport.requests import Request
from google.oauth2 import credentials, id_token

ENV_VAR_GCP_TARGET_SERVICE_ACCOUNT = "GCP_IMPERSONATE_SERVICE_ACCOUNT"
ENV_VAR_GOOGLE_APPLICATION_CREDENTIALS = "GOOGLE_APPLICATION_CREDENTIALS"
DEFAULT_SCOPES_FOR_IMPERSONATED_SERVICE_ACCOUNT = [
    "openid",
    "email",
    "https://www.googleapis.com/auth/iam",
    "https://www.googleapis.com/auth/cloud-platform",
]


class InvalidCredentialsOAuth2(Exception):
    pass


class ServiceAccountCredentials:

    """
    Handle Service Account discovery in local and remote environments
    export GCP_IMPERSONATE_SERVICE_ACCOUNT=precis-attribution@appspot.gserviceaccount.com
    Behavior
     - If local set GCP_IMPERSONATE_SERVICE_ACCOUNT to the name of the service account you want to impersonate.
     - If Environment variables arent set will default to ADC Credentials
      - Will infer service account from compute engine service account if available
      - Will use service account defined by GOOGLE_APPLICATION_CREDENTIALS
    Args:
        target_service_account: str e.g. "precis-attribution@appspot.gserviceaccount.com"
            if not explicitly set will infer from GCP_IMPERSONATE_SERVICE_ACCOUNT
    """

    def __init__(self, target_service_account: Optional[str] = None):

        self.target_service_account = target_service_account or os.environ.get(ENV_VAR_GCP_TARGET_SERVICE_ACCOUNT)
        logging.info(f"Impersonating Service Account: {self.target_service_account}")

        if self.target_service_account and os.environ.get(ENV_VAR_GOOGLE_APPLICATION_CREDENTIALS):
            logging.warning(f"WARNING: Both Service Account Impersonation and Service Account ADC variables are set.")

    def _get_impersonated_credentials(self, scopes: List[str] = []) -> impersonated_credentials.Credentials:
        """
        Args:
            scopes: List[str] e.g. ["https://www.googleapis.com/auth/spreadsheets.readonly"]
             scopes are passed from self.get_credentials
        """

        source_credentials, _ = google.auth.default()
        target_scopes = list(set((DEFAULT_SCOPES_FOR_IMPERSONATED_SERVICE_ACCOUNT[:] + scopes)))
        target_impersonated_credentials = impersonated_credentials.Credentials(
            source_credentials=source_credentials,
            target_principal=self.target_service_account,
            target_scopes=target_scopes,
            lifetime=3600,
        )
        target_impersonated_credentials.refresh(Request())
        return target_impersonated_credentials

    def _get_impersonated_id_token_credentials(
        self,
        target_audience: str = "https://www.example.com",
    ) -> impersonated_credentials.IDTokenCredentials:

        """
        Args:
            target_audience: str e.g. "https://www.example.com", or IAP Client ID
        """

        idt_credentials = impersonated_credentials.IDTokenCredentials(
            target_credentials=self._get_impersonated_credentials(),
            target_audience=target_audience,
            include_email=True,
        )
        idt_credentials.refresh(Request())
        return idt_credentials

    def get_credentials(self, scopes: List[str] = []) -> google.auth.credentials.Credentials:
        """
        Will return impersonated credentials if set and user is authorized otherwise will use ADC Credentials.
        If ADC credentials are OAuth2 credentials will raise an error, since these are not valid Service Account Credentials
         Args:
            scopes: List[str] e.g. ["https://www.googleapis.com/auth/spreadsheets.readonly"]
                the following scopes are set by default:
                [
                    "openid",
                    "email",
                    "https://www.googleapis.com/auth/iam",
                    "https://www.googleapis.com/auth/cloud-platform",
                ]
        """

        if self.target_service_account:
            creds = self._get_impersonated_credentials(scopes=scopes)
        else:
            source_credentials, _ = google.auth.default()
            if isinstance(source_credentials, credentials.Credentials):
                raise InvalidCredentialsOAuth2(
                    f"ADC are OAuth Credentials set env var for {ENV_VAR_GOOGLE_APPLICATION_CREDENTIALS} or {ENV_VAR_GCP_TARGET_SERVICE_ACCOUNT}"
                )
            creds = source_credentials
        logging.info(f"Fetched credentials for Service Account: {creds.service_account_email}")
        return creds

    def get_identity_token(self, target_audience: str):
        if self.target_service_account:
            id_token_credentials = self._get_impersonated_id_token_credentials(target_audience=target_audience)
            return id_token_credentials.token
        return id_token.fetch_id_token(Request(), audience=target_audience)


if __name__ == "__main__":

    def test_sa():
        PRECIS_CENTRAL_AUDIENCE = os.environ.get("PRECIS_CENTRAL_AUDIENCE")

        sac = ServiceAccountCredentials()  # target_service_account="precis-central@appspot.gserviceaccount.com")
        # service_account_credentials = sac.get_credentials()
        token = sac.get_identity_token(target_audience=PRECIS_CENTRAL_AUDIENCE)
        url = "https://precis-central.ew.r.appspot.com/api/hello"
        resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
        print("test_sa", resp.status_code, resp.json())

    test_sa()