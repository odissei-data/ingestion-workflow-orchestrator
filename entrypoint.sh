#!/usr/bin/env sh

prefect config set PREFECT_API_URL="http://0.0.0.0:4200/api"
prefect server start --host 0.0.0.0
