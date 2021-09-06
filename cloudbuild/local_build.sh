#!/usr/bin/env bash

source ./scripts/set_env.sh

read -p "Do Dry Run? (If N, will run actual build/deploy, else will just validate syntax? Y/N " -n 1 -r
echo
if [[ $REPLY =~ ^[Yn]$ ]]
then
  DRY_RUN=false
else
  DRY_RUN=true
fi

# https://cloud.google.com/cloud-build/docs/build-debug-locally
cloud-build-local \
  --config ./cloudbuild/cloudbuild.yaml \
  --dryrun=$DRY_RUN \
  --substitutions BRANCH_NAME=$(git branch --show-current),SHORT_SHA="local-build" \
  . # source of code
