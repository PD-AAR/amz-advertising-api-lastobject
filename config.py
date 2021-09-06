import os

import yaml

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Load in project_id vars
with open(os.path.join(ROOT_DIR, "pd_service.yml"), "r") as yaml_file:
    PROJECT_CONFIG = yaml.safe_load(yaml_file)


# GCP Config Variables, these are set automatically when deployed on GCP, load in from pd_service.yml if local
# https://cloud.google.com/run/docs/reference/container-contract#env-vars
# https://cloud.google.com/appengine/docs/standard/python3/runtime#environment_variables
# https://cloud.google.com/functions/docs/env-var#runtime_environment_variables_set_automatically
GCP_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT") or PROJECT_CONFIG["GCP_PROJECT"]
SERVICE_NAME = (
    os.environ.get("K_SERVICE")
    or os.environ.get("FUNCTION_NAME")
    or os.environ.get("GAE_SERVICE")
    or PROJECT_CONFIG["SERVICE_NAME"]
)
SERVICE_VERSION = (
    os.environ.get("K_REVISION")
    or os.environ.get("GAE_VERSION")
    or os.environ.get("X_GOOGLE_FUNCTION_VERSION")
    or "local"
)

# Manual env var set on deployment (prod, dev, etc.)
SERVICE_INSTANCE = os.environ.get("SERVICE_INSTANCE", "local")

# Central App
GAE_SERVICE_PRECIS_CENTRAL = PROJECT_CONFIG["GAE_SERVICE_PRECIS_CENTRAL"]
GAE_SERVICE_PRECIS_CENTRAL_CLIENT_ID = PROJECT_CONFIG["GAE_SERVICE_PRECIS_CENTRAL_CLIENT_ID"]

# Other project constants below
ROLLBAR_TOKEN = PROJECT_CONFIG["ROLLBAR_TOKEN"]
