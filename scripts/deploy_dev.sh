#!/usr/bin/env bash

source ./scripts/set_env.sh

# Docs: https://cloud.google.com/sdk/gcloud/reference/functions/deploy
gcloud functions deploy amz-advertising-api-lastobject-DEV \
  --project=$GCP_PROJECT \
  --entry-point=main \
  --runtime=python38 \
  --timeout=300 \
  --memory=128MB \
  --max-instances=50 \
  --region=$GCP_REGION \
  --service-account=$SERVICE_ACCOUNT_EMAIL \
  --trigger-http
  