# Managing Service Resources with gcloud

Infrastructure as Code (IaC) is the management of infrastructure (deployments and resources like tasks queues or service accounts, and their configuration settings) in a descriptive configuration model under source control.
This makes it easy to document, test, update, destroy, and move the configuration of a given Service or Application, and the resources it needs to function.

gcloud CLI provides convenient ways to interact with GCP resources. By using gcloud scripts to create/update resources we can commit them to version control and document the necessary components and configuration for a given project.

## Contents
- NOTE: in order to run these scripts your environment must be authenticated with an account that has access to perform these actions in GCP
    - `source ./scripts/auth_as_dev_account.sh` helper script to authenticate your session with the email you specified there
- `./gcloud/create_service_account.sh` will create the service account specified in the `pd_service.yml` file in the project root
    - it will also run the below `add_roles_to_service_account.sh`
- `./gcloud/add_roles_to_service_account.sh` will add IAM Roles to the service account, by default this is empty but with some examples. You can add roles there as needed and run the script by itself to update the Roles granted to the Service Account
- `./gcloud/destroy.sh` will delete the service account and any other resources created/updated in other scripts in this `gcloud` directory
    - NOTE: this is a static script, if more scripts are added to this directory or manually created, this destroy script will not know. It must be manually updated to add resources to destroy when ran.
    - NOTE: this script will not destroy the deployed service (GCF, GAE, GCR), instead use the `./scripts/tear_down.sh` to first destroy the deployed service, which then calls this script