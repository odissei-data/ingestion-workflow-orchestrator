# Django and Docker commands
include .env

PROJECT_NAME = prefect_docker
PROJECT_SRV = ${PROJECT_NAME}

.PHONY = help
.DEFAULT:
	@echo "Usage: "
	@make help

help: ## Show this help.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$|^[a-zA-Z_-]+:.*$$' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
build: ## Build and start project.
	@docker-compose up --build --detach
	make submodules
start: ## Start project running in a non-detached mode.
	@docker-compose up
startbg: ## Start project running in detached mode - background.
	@docker-compose up -d
stop: ## Stop the running project.
	@docker-compose stop
down: ## Downs the running project.
	@docker-compose down
dev-build: ## Build and start the dev setup.
	make submodules
	make network network_name=ingest
	@docker-compose up --build -d
	make network-add network_name=ingest container_name=prefect
	@docker-compose -f docker-compose-dev.yml up --build -d
dev-start: ## Start the ingest services.
	@docker-compose -f docker-compose-dev.yml up
dev-down: ## Down the ingest services.
	make down
	@docker-compose -f docker-compose-dev.yml down
network: ## Creates the ingest network.
	@if [ -z $$(docker network ls -q -f name=${network_name}) ]; then \
        docker network create ${network_name}; \
        echo "Network ${network_name} created."; \
    else \
        echo "Network ${network_name} already exists."; \
    fi
network-add: ## Add a container to the ingest network.
	@docker network connect ${network_name} ${container_name}
shell-be: ## Enter system shell in backend container
	@docker-compose exec prefect bash
python-shell-be: ## Enter into IPython shell in backend container
	@docker-compose exec prefect python -m IPython
submodules: ## Sets up the submodules and checks out their main branch.
	git submodule init
	git submodule foreach git checkout main	
run: ## Runs a given flow in prefect. eg: make run workflow_name="main_cbs_ingestion.py" args="--target_url https://portal.devstack.odissei.nl --target_key api_key"
	@docker exec -it ${PROJECT_CONTAINER_NAME} python flows/entry_workflows/${workflow_name} ${args}
deploy-flows: ## Deploys all ingestion workflows to the prefect server.
	@docker exec -it prefect python deployment/dedockploy_ingestion_pipelines.py