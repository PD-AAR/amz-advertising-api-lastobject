# amz-advertising-api-lastobject

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
![Coverage](static/images/coverage-badge.svg)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

Generated from [Precis GCP Micoservices Chassis](https://github.com/Precis-Digital/precis-gcp-worker-template) (VERSION: beta) via [Cookiecutter](https://cookiecutter.readthedocs.io/en/latest/README.html)


## Prerequisites:
- [python](https://www.python.org/downloads/) and virtual environment manager of your choice
- [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install)


## Setup
- Create/activate a virtual environment
- Edit [`./scripts/TEMPLATE_auth_as_dev_account.sh`](scripts/TEMPLATE_auth_as_dev_account.sh) by adding your email in the file and saving a copy without "TEMPLATE_" prefix
    - test out with `source ./scripts/auth_as_dev_account.sh`
- `pip install -r requirements-dev.txt`
- `pre-commit install` (optional)
- Optionally fill in Service configuration in [pd_service.yml](pd_service.yml) (GCP Project ID, Region, etc.)
- Develop!
    - Run tests by executing `./scripts/run_tests.sh`
    - Run locally by executing  `./scripts/run_locally.sh`


## Deploy
- Edit [pd_service.yml](pd_service.yml) and enter desired target GCP Project ID, Region, etc. 
- From root, in a session authenticated as user with access to target GCP Project
    - `source ./scripts/auth_as_dev_account.sh` helper script to authenticate your session with the email you specified there
- `./gcloud/create_service_account.sh`
- Deploy!
    - `./scripts/deploy_dev.sh` - deploys a 'non-production' instance (GCR and GAE - a 'no traffic' deployment, GCF - a separate function with suffix)
    - `./scripts/deploy_prod.sh` - deploys a 'production' instance (100% of traffic)


## Core Contents
<details>
  <summary>Click to expand details</summary>
  
  - [pd_service.yml](pd_service.yml) - Project/Service level configuration, read in from scripts and application runtime
  - [config.py](config.py) - Application level configuration, reads pd_service.yml, and adds any values specific to application logic
  - [main.py](main.py) - Main Application entrypoint
  - [utils](pd_utils):
    - [flask_utils](pd_utils/flask_utils.py) - Flask utilities, ex. method decorators to restrict endpoints to cloud tasks, or specific domains or users, etc.
    - [logging_utils](pd_utils/logging_utils.py) - Logging utilities, ex. setting logging format with cloud traces
    - [monitoring_utils](pd_utils/monitoring_utils.py) - Monitoring utilities, ex. helper functions to setup [rollbar](https://rollbar.com/) error alerts
  - [tests](tests) - test folder with base tests, demos basic testing
  - [scripts](scripts):
    - `source ./scripts/set_env.sh` to read in `pd_service.yml` (all other `.sh` files in scripts directory source `set_env.sh`)
    - `source ./scripts/auth_as_dev_account.sh`to authenticate gcloud as yourself and source set_env.sh (can then skip above step)
    - `./scripts/run_locally.sh` runs app locally, adding a  `--run-as-prod` flag sets an env var SERVICE_INSTANCE="prod",
which can be used in application logic. In deployment scripts this value is set.
    - `./scripts/deploy_prod.sh` and `./scripts/deploy_dev.sh` deploy the service, optional flag for `--version=` (defaults to "deployed-TIMESTAMP")
        - `deploy_prod.sh` sets traffic to 100%
        - `deploy_dev.sh` sends no traffic
    - `./scripts/replay_project_gen.sh` will replay the cookiecutter project generation, allowing different options to be selected
        - NOTE: this will overwrite files and should be done in a separate branch for safety. See template repo for detailed instructions
    - `./scripts/tear_down.sh` will destroy the project, deleting or removing the deployed service, service account, any other resources managed here
    - `./scripts/build_local_image.sh` can be used to use [pack CLI](https://buildpacks.io/docs/tools/pack/) 
to build a local Docker image with GCP native cloud buildpacks, could then use docker to run the image locally
        - Requires installing [pack CLI](https://buildpacks.io/docs/tools/pack/) and [docker](https://docs.docker.com/get-docker/)
        - Add `--override-default-proc` flag to override normal build and generate image that runs tests before running web process (for testing purposes only)
  - [cloudbuild](cloudbuild) - for adding CI/CD to project, or using Cloud Build to deploy:
    - [cloudbuild.yaml](cloudbuild/cloudbuild.yaml) - Cloud Build configuration / steps
    - [submit_build.sh](cloudbuild/submit_build.sh) - Manually submit a build to Cloud Build
    - [local_build.sh](cloudbuild/local_build.sh) - Run build locally
        - Requires [gcloud cloud-build-local](https://cloud.google.com/build/docs/build-debug-locally) component
        - Will prompt to do dry run (only validates syntax), if not, will perform full build including any deployment steps
    - For adding CI/CD - add dev and prod [GitHub Build Triggers](https://cloud.google.com/build/docs/automating-builds/create-github-app-triggers):
        - `./cloudbuild/create_update_dev_build_trigger.sh` create/updates GitHub Build trigger on Pull Request to master
        - `./cloudbuild/create_update_prod_build_trigger.sh` create/updates GitHub Build trigger on pushes to master
        - Configuration for the prod and dev GitHub Cloud Build triggers are in `cloudbuild/dev_build_trigger.yaml` and `cloudbuild/prod_build_trigger.yaml`
        - cloudbuild.yaml makes use of same deployment scripts in scripts directory (`deploy_prod.sh` when on master branch, `deploy_dev.sh` on others)

</details>


## Notes / Docs:
- Uses:
    - [Pre-commit](https://pre-commit.com/) for Git pre-commit hooks
    - [Black](https://github.com/psf/black) for python code formatting
    - [isort](https://github.com/PyCQA/isort) to sort imports
    - [Unittest](https://docs.python.org/3/library/unittest.html) as test runner (default)
    - [Coverage](https://coverage.readthedocs.io/en/coverage-5.3.1/) for assessing test coverage