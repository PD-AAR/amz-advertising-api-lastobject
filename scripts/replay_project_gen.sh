#!/usr/bin/env bash

cookiecutter git+ssh://git@github.com/Precis-Digital/precis-gcp-worker-template.git \
  --output-dir .. \
  --config-file .cookiecutter.yaml \
  --overwrite-if-exists