#!/usr/bin/env bash

source ./scripts/set_env.sh

# Run locally with Google Functions Framework
# https://github.com/GoogleCloudPlatform/functions-framework-python
functions-framework --target=main --debug --signature-type=http --host=0.0.0.0 --port=8080
