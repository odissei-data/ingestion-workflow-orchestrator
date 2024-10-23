#!/usr/bin/env sh

prefect config set PREFECT_API_URL="http://prefect:4200/api"
prefect worker start --pool default