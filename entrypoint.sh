#!/usr/bin/env sh

prefect config set PREFECT_API_URL="http://0.0.0.0:4200/api"
prefect config set PREFECT_UI_STATIC_DIRECTORY="/app/"
prefect server start --host 0.0.0.0