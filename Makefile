# Django and Docker commands
include .env

PROJECT_NAME = prefect_docker
PROJECT_SRV = ${PROJECT_NAME}

.PHONY = help
.DEFAULT:
	@echo "Usage: "
	@make help

help: ## Show this help.
	# From https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
build: ## Build and start project.
	@docker-compose up --build --detach
	make submodules
buildprod: ## Build and start project using production docker-compose
	@docker-compose -f docker-compose-prod.yml up --build
start: ## Start project running in a non-detached mode.
	@docker-compose up
startbg: ## Start project running in detached mode - background.
	@docker-compose up -d
startprodbg: ## Start product in production mode, in background.
	@docker-compose -f docker-compose-prod.yml up -d
stop: ## Stop the running project.
	@docker-compose stop
copy-poetry-files: ## Copies poetry files inside container
	@docker cp ./prefect_docker/pyproject.toml ${PROJECT_CONTAINER_NAME}:/pyproject.toml
	@docker cp ./prefect_docker/poetry.lock ${PROJECT_CONTAINER_NAME}:/poetry.lock
	@docker exec -it ${PROJECT_CONTAINER_NAME} poetry update
save-poetry-files: ## Exports poetry files from inside container
	@docker cp ${PROJECT_CONTAINER_NAME}:/pyproject.toml ./prefect_docker/pyproject.toml.new
	@docker cp ${PROJECT_CONTAINER_NAME}:/poetry.lock ./prefect_docker/poetry.lock.new
update-requirements: 
	make copy-poetry-files 
	make save-poetry-files
add-poetry-package: copy-poetry-files ## Adds a poetry package, using backend container to resolve. Expects: package_name arg. Ex: make add-poetry-package package_name="foo"
	@docker exec -it ${PROJECT_CONTAINER_NAME} poetry add ${package_name}
	export-poetry-files
remove-poetry-package: copy-poetry-files ## Removes a poetry package. Similar to adding.
	@docker exec -it ${PROJECT_CONTAINER_NAME} poetry remove ${package_name}
	export-poetry-files
shell-be: ## Enter system shell in backend container
	@docker-compose exec prefect bash
python-shell-be: ## Enter into IPython shell in backend container
	@docker-compose exec prefect python -m IPython
submodules:
	git submodule init
	git submodule foreach git checkout main	
run:
	@docker exec -it ${PROJECT_CONTAINER_NAME} python /scripts/${workflow_name}
