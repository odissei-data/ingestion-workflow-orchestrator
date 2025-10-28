# Django and Docker commands
include .env

PROJECT_NAME = prefect_docker
PROJECT_SRV = ${PROJECT_NAME}
TARGET_URL ?=
TARGET_KEY ?=
TARGET_BUCKET ?=
DO_HARVEST ?= True
FULL_HARVEST ?= False

.PHONY = help
.DEFAULT:
	@echo "Usage: "
	@make help

help: ## Show this help.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$|^[a-zA-Z_-]+:.*$$' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
build: ## Build and start project.
	make submodules
	@docker compose up --build --detach
start: ## Start project running in a non-detached mode.
	@docker compose up
startbg: ## Start project running in detached mode - background.
	@docker compose up -d
stop: ## Stop the running project.
	@docker compose stop
down: ## Downs the running project.
	@docker compose down
dev-build: ## Build and start the dev setup.
	make setup-secrets
	make submodules
	make setup-skosmos
	make network network_name=ingest
	@docker compose up --build -d
	make network-add network_name=ingest container_name=prefect
	@docker compose -f docker-compose-dev.yml up --build -d
dev-full-build: ## Build and start the full dev setup including ODISSEI Dataverse portal.
	make setup-secrets
	make submodules
	make setup-skosmos
	make setup-dataverse-stack
	make network network_name=ingest
	@echo ""
	@echo "========================================="
	@echo "Starting ODISSEI Dataverse stack..."
	@echo "This will take several minutes..."
	@echo "========================================="
	@echo ""
	@if [ -f "odissei-dataverse-stack/.env" ]; then \
		cd odissei-dataverse-stack && yes | bash setup.sh; \
	else \
		echo "Error: odissei-dataverse-stack/.env not found!"; \
		exit 1; \
	fi
	@echo ""
	@echo "========================================="
	@echo "Dataverse stack started successfully!"
	@echo "Extracting API key..."
	@echo "========================================="
	@echo ""
	make extract-dataverse-apikey
	@echo ""
	@echo "========================================="
	@echo "Building and starting Prefect services..."
	@echo "========================================="
	@echo ""
	@docker compose up --build -d
	@sleep 5
	make network-add network_name=ingest container_name=prefect
	make network-add network_name=dataverse container_name=prefect
	make network-add network_name=dataverse container_name=prefect-worker
	@docker compose -f docker-compose-dev.yml up --build -d
	@echo ""
	@echo "========================================="
	@echo "✓ Full dev setup complete!"
	@echo "========================================="
	@echo ""
	@echo "Available services:"
	@echo "  - Dataverse UI:          http://localhost:8080"
	@echo "  - Prefect UI:            http://localhost:4200"
	@echo "  - Skosmos:               http://localhost:9090"
	@echo "  - Fuseki:                http://localhost:9030"
	@echo ""
dev-start: ## Start the ingest services.
	@docker compose -f docker-compose-dev.yml up
dev-down: ## Down the ingest services.
	make down
	@docker compose -f docker-compose-dev.yml down
dev-full-down: ## Down the full dev setup including ODISSEI Dataverse stack.
	@echo "Stopping all services..."
	@docker compose down 2>/dev/null || true
	@docker compose -f docker-compose-dev.yml down 2>/dev/null || true
	@if [ -d "odissei-dataverse-stack" ]; then \
		echo "Tearing down ODISSEI Dataverse stack..."; \
		echo "Stopping Dataverse containers..."; \
		docker compose -f odissei-dataverse-stack/utils/dataverse/docker-compose.yml down -v 2>/dev/null || true; \
		echo "Stopping Traefik containers..."; \
		docker compose -f odissei-dataverse-stack/utils/traefik/docker-compose.yml down -v 2>/dev/null || true; \
		if [ -f "odissei-dataverse-stack/teardown_and_cleanup_submodules.sh" ]; then \
			echo "Running cleanup script..."; \
			cd odissei-dataverse-stack && echo "y" | bash teardown_and_cleanup_submodules.sh || true; \
		else \
			echo "Teardown script not found, skipping..."; \
		fi; \
	fi
	@if [ -d "odissei-dataverse-stack" ]; then \
		echo "Removing odissei-dataverse-stack directory..."; \
		docker run --rm -v "$$(pwd):/workspace" -w /workspace alpine:latest rm -rf odissei-dataverse-stack || \
		sudo rm -rf odissei-dataverse-stack || \
		echo "⚠️  Could not remove odissei-dataverse-stack directory. You may need to run: sudo rm -rf odissei-dataverse-stack"; \
	fi
	@echo "Services stopped."
clean-all: ## Complete cleanup - removes all generated files and Docker resources (USE WITH CAUTION).
	@echo "⚠️  WARNING: This will remove all generated files and Docker resources!"
	@echo "Press Ctrl+C within 5 seconds to cancel..."
	@sleep 5
	@echo "Proceeding with cleanup..."
	make dev-full-down
	@echo "Removing generated directories..."
	@rm -rf odissei-dataverse-stack
	@rm -rf skosmos-data skosmos-config
	@rm -rf docker-dev-volumes
	@echo "Removing Docker volumes..."
	@docker volume rm $$(docker volume ls -q | grep -E 'prefectdb|fuseki-data|skosmos-configuration|harvester-db-data|dataverse') 2>/dev/null || true
	@echo "Removing Docker networks..."
	@docker network rm ingest traefik dataverse 2>/dev/null || true
	@echo "✓ Complete cleanup finished. Run 'make dev-build' or 'make dev-full-build' to start fresh."
network: ## Creates the ingest network.
	@if [ -z $$(docker network ls -q -f name=${network_name}) ]; then \
        docker network create ${network_name}; \
        echo "Network ${network_name} created."; \
    else \
        echo "Network ${network_name} already exists."; \
    fi
network-add: ## Add a container to the ingest network.
	@if [ $$(docker network inspect -f '{{range .Containers}}{{.Name}} {{end}}' ${network_name} | grep -w ${container_name}) ]; then \
		echo "Container ${container_name} is already connected to network ${network_name}."; \
	else \
		docker network connect ${network_name} ${container_name}; \
		echo "Container ${container_name} connected to network ${network_name}."; \
	fi

shell-be: ## Enter system shell in backend container
	@docker compose exec prefect bash
python-shell-be: ## Enter into IPython shell in backend container
	@docker compose exec prefect python -m IPython
submodules: ## Sets up the submodules and checks out their main branch.
	git submodule init
	git submodule update --remote
	git submodule foreach git checkout main
	git submodule foreach git pull origin main
setup-secrets: ## Sets up .secrets.toml from example if it doesn't exist.
	@if [ ! -f "scripts/configuration/.secrets.toml" ]; then \
		echo "Creating .secrets.toml from secrets_example.toml..."; \
		cp scripts/configuration/secrets_example.toml scripts/configuration/.secrets.toml; \
		echo ".secrets.toml created. Please update with your actual secrets."; \
	else \
		echo ".secrets.toml already exists."; \
	fi
setup-skosmos: ## Sets up Skosmos vocabulary data and configuration files.
	@echo "Setting up Skosmos data and configuration..."
	@if [ ! -d "skosmos-data" ] || [ -z "$$(ls -A skosmos-data)" ]; then \
		echo "Fetching Skosmos vocabulary data..."; \
		rm -rf /tmp/sd-skosmos-temp; \
		git clone --depth 1 https://github.com/odissei-data/sd-skosmos.git /tmp/sd-skosmos-temp; \
		mkdir -p skosmos-data; \
		cp -r /tmp/sd-skosmos-temp/data/* skosmos-data/ 2>/dev/null || echo "No data files found"; \
		mkdir -p skosmos-config; \
		cp -r /tmp/sd-skosmos-temp/config/* skosmos-config/ 2>/dev/null || echo "No config files found"; \
		rm -rf /tmp/sd-skosmos-temp; \
		echo "Skosmos data and config setup complete."; \
	else \
		echo "Skosmos data already exists, skipping setup."; \
	fi
setup-dataverse-stack: ## Clones and sets up the ODISSEI Dataverse stack.
	@echo "Setting up ODISSEI Dataverse stack..."
	@if [ ! -d "odissei-dataverse-stack" ]; then \
		echo "Cloning odissei-dataverse-stack repository..."; \
		git clone https://github.com/odissei-data/odissei-dataverse-stack.git; \
		cd odissei-dataverse-stack && \
		echo "Creating .env file for local development..." && \
		cp dot_env_example .env && \
		sed -i 's|ROOT_URL=.*|ROOT_URL="http://localhost:8080"|g' .env && \
		sed -i 's|HOSTNAME=.*|HOSTNAME="localhost"|g' .env && \
		echo "ODISSEI Dataverse stack setup complete."; \
	else \
		echo "ODISSEI Dataverse stack already exists, updating..."; \
		cd odissei-dataverse-stack && \
		if [ ! -f ".env" ]; then \
			echo "Creating missing .env file..."; \
			cp dot_env_example .env && \
			sed -i 's|ROOT_URL=.*|ROOT_URL="http://localhost:8080"|g' .env && \
			sed -i 's|HOSTNAME=.*|HOSTNAME="localhost"|g' .env; \
		fi; \
	fi
extract-dataverse-apikey: ## Extracts API key from Dataverse database and updates .secrets.toml.
	@echo "Extracting Dataverse API key from database..."
	@sleep 5
	@CONTAINER_NAME=$$(docker ps --filter "name=postgres" --format "{{.Names}}" | head -1); \
	if [ -z "$$CONTAINER_NAME" ]; then \
		echo "Error: No PostgreSQL container found. Please ensure Dataverse is running."; \
		exit 1; \
	fi; \
	echo "Using PostgreSQL container: $$CONTAINER_NAME"; \
	DB_USER=$$(docker exec $$CONTAINER_NAME env | grep POSTGRES_USER | cut -d= -f2); \
	if [ -z "$$DB_USER" ]; then DB_USER="dataverse"; fi; \
	API_KEY=$$(docker exec $$CONTAINER_NAME psql -U $$DB_USER -d dataverse -t -c "SELECT u.useridentifier, t.tokenstring FROM authenticateduser u JOIN apitoken t ON u.id = t.authenticateduser_id LIMIT 1;" 2>/dev/null | awk '{print $$NF}' | xargs); \
	if [ -n "$$API_KEY" ] && [ "$$API_KEY" != "" ]; then \
		echo "API Key found: $$API_KEY"; \
		echo "Updating .secrets.toml with extracted API key..."; \
		sed -i.bak 's#DESTINATION_DATAVERSE_API_KEY="[^"]*"#DESTINATION_DATAVERSE_API_KEY="'"$$API_KEY"'"#g' scripts/configuration/.secrets.toml; \
		rm -f scripts/configuration/.secrets.toml.bak; \
		echo "API key updated in .secrets.toml"; \
		echo "Rebuilding Prefect containers with new configuration..."; \
		docker compose build prefect prefect-worker; \
		echo "✓ API key configuration complete!"; \
	else \
		echo "⚠ No API key found in database. Dataverse may not be fully initialized yet."; \
		echo "  Waiting 30 seconds and trying again..."; \
		sleep 30; \
		API_KEY=$$(docker exec $$CONTAINER_NAME psql -U $$DB_USER -d dataverse -t -c "SELECT u.useridentifier, t.tokenstring FROM authenticateduser u JOIN apitoken t ON u.id = t.authenticateduser_id LIMIT 1;" 2>/dev/null | awk '{print $$NF}' | xargs); \
		if [ -n "$$API_KEY" ] && [ "$$API_KEY" != "" ]; then \
			echo "API Key found: $$API_KEY"; \
			sed -i.bak 's#DESTINATION_DATAVERSE_API_KEY="[^"]*"#DESTINATION_DATAVERSE_API_KEY="'"$$API_KEY"'"#g' scripts/configuration/.secrets.toml; \
			rm -f scripts/configuration/.secrets.toml.bak; \
			docker compose build prefect prefect-worker; \
			echo "✓ API key configuration complete!"; \
		else \
			echo "⚠ Still no API key found. You can run 'make extract-dataverse-apikey' manually after Dataverse is ready."; \
		fi; \
	fi
ingest: ## Runs the ingest workflow for a specified data provider. The url and key of the target can be optionally added. eg: make ingest data_provider=CBS TARGET_URL=https://portal.example.odissei.nl TARGET_KEY=abcde123-11aa-22bb-3c4d-098765432abc
	@docker exec -it ${PROJECT_CONTAINER_NAME} python run_ingestion.py --data_provider=$(data_provider) --target_url=$(TARGET_URL) --target_key=$(TARGET_KEY) --target_bucket=$(TARGET_BUCKET) --do_harvest=$(DO_HARVEST) --full_harvest=$(FULL_HARVEST)
deploy: ## Deploys all ingestion workflows to the prefect server.
	@docker exec -it prefect python deployment/deploy_ingestion_pipelines.py