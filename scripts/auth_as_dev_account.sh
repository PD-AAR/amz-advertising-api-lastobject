#!/usr/bin/env bash

source ./scripts/set_env.sh

# TODO: add your email address for local development
DEV_ACCNT_EMAIL="jonas@precisdigital.com"

echo "Login gcloud as Developer's Account"

# Authorize gcloud with developer's account (used to deploy, create, remove GCP assets)
gcloud auth login $DEV_ACCNT_EMAIL --update-adc

gcloud config set project $GCP_PROJECT