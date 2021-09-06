#!/usr/bin/env bash

source ./scripts/set_env.sh

read -p "WARNING - this will remove/delete any created resources (Services, Service Accounts, etc.) - Proceed? Y/N " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
  echo "Tearing down project resources!"
  echo "NOTE: this does not include any Cloud Build Triggers that were created, you must manually delete these (for now)"

  echo "Tearing down service"

  # Delete Cloud Function
  gcloud functions delete $SERVICE_NAME \
    --region=$GCP_REGION \
    --project=$GCP_PROJECT

  echo "Tearing down resources"

  echo "Destroying Resources with gcloud"
  source ./scripts/gcloud/destroy.sh

else
  echo "Tear down aborted by user"
fi
