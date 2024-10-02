#!/usr/bin/env sh

prefect config set PREFECT_API_URL="http://prefect-houston:4200/api"
sleep 10
prefect worker start --pool default
