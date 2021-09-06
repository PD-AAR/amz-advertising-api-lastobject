#!/usr/bin/env bash

source ./scripts/set_env.sh

# Destroy GCP Resources listed below
read -p "WARNING - Delete Service Account?  (N to abort and continue with deletion of other resources) - Y/N " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
  gcloud iam service-accounts delete $SERVICE_ACCOUNT_EMAIL --project=$GCP_PROJECT
fi

## When deploying a Cloud Function with PubSub trigger, a Subscription Topic is auto-created in this convention
#gcloud pubsub subscriptions delete gcf-$SERVICE_NAME-$GCP_REGION-$PUBSUB_TRIGGER_TOPIC-topic \
#  --project=$GCP_PROJECT