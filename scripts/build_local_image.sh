#!/usr/bin/env bash

set -e # exit if any commands fail

source ./scripts/set_env.sh

OVERRIDE_ENTRYPOINT=
IMAGE_NAME=$SERVICE_NAME

# Loop through passed arguments and process them
# https://pretzelhands.com/posts/command-line-flags
for arg in "$@"
do
  case $arg in
    # set instance as prod via env var
    --override-default-proc)
    echo "Building image with default process override"
    OVERRIDE_ENTRYPOINT="worker"
    IMAGE_NAME="$SERVICE_NAME-test"
    ;;
    -h|--help)
    echo "add --override-default-proc flag to override default process from Procfile"
    exit
    ;;
  esac
done

# Buildpacks docs:
# https://buildpacks.io/docs/tools/pack/
# https://github.com/GoogleCloudPlatform/buildpacks/blob/main/README.md

pack build $IMAGE_NAME --builder gcr.io/buildpacks/builder:v1 \
  --clear-cache \
  --env "GOOGLE_FUNCTION_TARGET=main" \
  --env "GOOGLE_FUNCTION_SIGNATURE_TYPE=http" \
  --default-process=$OVERRIDE_ENTRYPOINT



# can then run via
#docker run --name $SERVICE_NAME --rm -p 8080:8080 $SERVICE_NAME

# or start interactive session
#docker run -it --rm --entrypoint /bin/bash $SERVICE_NAME

# could also publish to container registry by adding publish flag
#pack build --builder gcr.io/buildpacks/builder:v1 --publish gcr.io/YOUR_PROJECT_ID/APP_NAME