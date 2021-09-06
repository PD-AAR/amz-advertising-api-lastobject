#!/usr/bin/env bash

source ./scripts/set_env.sh

# https://cloud.google.com/sdk/gcloud/reference/builds/submit
gcloud builds submit .\
  --config ./cloudbuild/cloudbuild.yaml \
  --project $GCP_PROJECT \
  --substitutions BRANCH_NAME=$(git branch --show-current),SHORT_SHA="local-build"
