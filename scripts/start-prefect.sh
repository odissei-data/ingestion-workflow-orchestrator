source .env

prefect config set PREFECT_API_DATABASE_CONNECTION_URL="$PREFECT_API_DATABASE_CONNECTION_URL"
prefect config set PREFECT_API_URL="http://0.0.0.0:4200/api"
prefect server start