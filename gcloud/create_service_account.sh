#!/usr/bin/env bash

source ./scripts/auth_as_dev_account.sh

# Create Service Account
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME --project=$GCP_PROJECT

# Allow developer to impersonate service account (generate temp tokens)
gcloud iam service-accounts add-iam-policy-binding $SERVICE_ACCOUNT_EMAIL \
 --member="user:$DEV_ACCNT_EMAIL" \
 --role="roles/iam.serviceAccountTokenCreator"

# Run script to add any specified roles to the account
source ./gcloud/add_roles_to_service_account.sh