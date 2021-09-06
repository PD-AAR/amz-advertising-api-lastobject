#!/usr/bin/env bash

source ./scripts/set_env.sh

echo "Adding IAM roles to " $SERVICE_ACCOUNT_EMAIL

# TODO: add any roles necessary for the service, examples below

## Grant Cloud Storage Admin to Svc Account (read and list buckets and blobs)
#gcloud projects add-iam-policy-binding $GCP_PROJECT \
#  --member serviceAccount:$SERVICE_ACCOUNT_EMAIL \
#  --role=roles/storage.admin
#
## Grant BigQuery Data Owner to Svc Account (create datasets)
#gcloud projects add-iam-policy-binding $GCP_PROJECT \
#  --member serviceAccount:$SERVICE_ACCOUNT_EMAIL \
#  --role=roles/bigquery.dataOwner
#
## Grant BigQury Job User to Svc Account (run jobs)
#gcloud projects add-iam-policy-binding $GCP_PROJECT \
#  --member serviceAccount:$SERVICE_ACCOUNT_EMAIL \
#  --role=roles/bigquery.jobUser


echo "Note! It can take a couple minuets for IAM Roles to update"