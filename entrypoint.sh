#!/usr/bin/env sh

prefect config set PREFECT_API_URL="${API_URL}"
prefect config set PREFECT_UI_STATIC_DIRECTORY="/app/"
prefect server start --host 0.0.0.0