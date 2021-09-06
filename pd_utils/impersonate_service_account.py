from typing import Optional

import google.auth
import requests
from google.auth import impersonated_credentials
from google.auth.transport.requests import Request
from google.oauth2 import id_token


def get_target_credentials(
    project_id: str,
    service_account: str,
    source_credentials: Optional[google.auth.credentials.Credentials] = None,
) -> google.auth.impersonated_credentials.Credentials:

    if source_credentials is None:
        source_credentials, _ = google.auth.default(quota_project_id=project_id)

    target_credentials = impersonated_credentials.Credentials(
        source_credentials=source_credentials,
        target_principal=service_account,
        target_scopes=[
            "openid",
            "email",
            "https://www.googleapis.com/auth/iam",
            "https://www.googleapis.com/auth/cloud-platform",
        ],
        lifetime=3600,
    )

    target_credentials.refresh(Request())

    return target_credentials


def get_target_id_token_credentials(
    target_credentials: google.auth.impersonated_credentials.Credentials,
    target_audience="https://example.com",
) -> google.auth.impersonated_credentials.IDTokenCredentials:
    idt_credentials = impersonated_credentials.IDTokenCredentials(
        target_credentials=target_credentials,
        target_audience=target_audience,
        include_email=True,
    )
    idt_credentials.refresh(Request())
    return idt_credentials


def verify_id_token(token, audience=None):
    request = google.auth.transport.requests.Request()
    result = id_token.verify_token(token, request)
    if result["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
        return False
    if audience != result["aud"]:
        return False
    return True


# print(idt_credentials.__dict__)

# def get_credentials_for_service_account_impersonation(service_account, client_id):
#    google_oauth_access_token=$(gcloud auth print-access-token --impersonate-service-account=$SVC_ACCNT_EMAIL)

if __name__ == "__main__":

    PRECIS_CENTRAL_AUDIENCE = "119500220010-0r41f87laae7eav7vcrp9a71dmnobdlg.apps.googleusercontent.com"

    target_credentials = get_target_credentials(
        project_id="precis-attribution",
        service_account="precis-attribution@appspot.gserviceaccount.com",
    )
    idt_credentials = get_target_id_token_credentials(
        target_credentials=target_credentials, target_audience=PRECIS_CENTRAL_AUDIENCE
    )
    idtoken = idt_credentials.token
    print(id_token.verify_token(idtoken, Request()))
    print(f"ID Token Valid: {verify_id_token(idtoken, audience=PRECIS_CENTRAL_AUDIENCE)}")

    url = "https://precis-central.ew.r.appspot.com/api/hello"
    resp = requests.get(url, headers={"Authorization": f"Bearer {idtoken}"})
    print(resp.status_code)
    print(resp.json())

    url = "https://task-manager-dot-precis-attribution.ew.r.appspot.com/api/tasks/task_manager_status?auth_account=analytics-no@precisdigital.com&job_id=5079229473488896"
    resp = requests.get(url, headers={"Authorization": f"Bearer {idtoken}"})
    print(resp.status_code)
    print(resp.json()["tasks"][0])
    import json

    # json.dump(resp.json(), open("task-manager-status.json", "w"))
