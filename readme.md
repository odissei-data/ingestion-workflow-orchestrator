# Prefect + Docker

A small project which contains two working parts:

- Prefect
- Docker

## Versioning and dependency management

- Python: Poetry
- Environment vars: .env
- Version control: git

# Development

If you want to develop new flows for the Ingestion Orchestrator you need to set
up your local environment first. Follow the step below, and you should be able
to start development.

First you need to get a couple of containers running. All of these are needed
as they are used by the Ingestion Orchestrator.

### Harvester

Harvesters are outside the scope of this project. As long as you have a couple
of `xml` files with metadata you are good to go.

### Dataverse

A local Dataverse instance makes it easy to deposit via the API.

https://github.com/IQSS/dataverse-docker

> Only a Super User can deposit via the API.

Set the `superuser` boolean to true in the `authenticateduser` table. You are
now a Super User. 

### Dataverse Importer

This service imports metadata into Dataverse.

https://github.com/odissei-data/dataverse-importer

### Publication Date Updater

Corrects the publication date of the imported metadata.

https://github.com/odissei-data/publication-date-updater

### Metadata Fetcher

Fetches the metadata of a dataset from a Dataverse.

https://github.com/odissei-data/dataverse-metadata-fetcher

### Dataverse Mapper

Maps any JSON to Dataverse's JSON format.

https://github.com/odissei-data/dataverse-mapper

### Dans Transformer Service

Transforms from XML to JSON (or from/to other formats).

https://github.com/ekoi/dans-transformer-service

> More info below on how to start this container.

### Metadata Refiner

Refines JSON metadata.

https://github.com/odissei-data/metadata-refiner

## Docker Network

To allow the containers to communicate with each other you need to create a
network. The commands below should do the trick.

```shell
docker network create -d bridge ingestion-network
docker network connect ingestion-network dataverse
docker network connect ingestion-network dataverse-importer
docker network connect ingestion-network publication-date-updater
docker network connect ingestion-network metadata-fetcher
docker network connect ingestion-network prefect
docker network connect ingestion-network dataverse-mapper-v2
docker network connect ingestion-network dans-transformer-service
docker network connect ingestion-network metadata-refiner
```

### Ports
The containers are assumed to be running on the following ports. If needed,
adjust the port numbers in the `.env` file.

- dataverse: 8080
- dataverse-importer: 8091
- metadata-fetcher: 8092
- publication-date-update: 8093
- dataverse-mapper-v2: 8094
- dans-transformer-service: 1745
- metadata-refiner: 7878

# Dynaconf

The Ingestion Workflow Orchestrator uses Dynaconf to manage its settings. This
chapter will give a very short introduction on Dynaconf. For more information
read the docs.

Use the `.env` file to set the environment to either development or production.

> ENV_FOR_DYNACONF=development


## Settings files

The settings are split into multiple toml files. This makes it easier to manage
a large amount of settings. You can specify which files are loaded in
`config.py`. The files are loaded in order and overwrite each other if they
share settings with the same name.

- settings.toml, contains the base settings
- .secrets.toml, contains all secrets
- <foo>_settings.toml, datastation specific settings

Each file is split into multiple sections: default, development, production.
Default settings are always loaded and usually contain one or more dynamic
parts using `@format`. Development and production contain the values that
depend on the current environment.

The example below shows how dynamic settings work. The metadata directory
changes based on the current environment.

```toml
[default]
"METADATA_DIRECTORY"="@format {this.METADATA_DIRECTORY}"

[development]
"METADATA_DIRECTORY"="path/to/local/dir"

[production]
"METADATA_DIRECTORY"="path/to/s3/bucket"
```



# Dans Transformer Service

The Dans Transformer Service container needs some manual configuration.

You need to create two files in the`src/conf` directory. Then you can run the
container with the following command.

`docker run -v /path/to/src/conf:/home/dans/dans-transformer-service/src/conf -d -p 1745:1745 --name dans-transformer-service ekoindarto/dans-transformer-service:0.5.2;`

**settings.toml**

```toml
[default]
#FastAPI
fastapi_title = "DANS Transformer Service"
fastapi_description = "This service supports .."

temp_transform_file = "/tmp/transform"
#logs
log_file = "../logs/dts.log"
log_level = 10
log_format = "%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s"
#Note: below the list of logging level
#CRITICAL = 50
#ERROR = 40
#WARNING = 30
#INFO = 20
#DEBUG = 10
#xsl location
saved_xslt_dir = "../saved-xsl"

#jinja template location
jinja_and_prop_dir = "../saved-templates"

[development]

[staging]

[testing]

[production]
```

**.secrets.toml**

```toml
[default]
dans_transformer_service_api_key = "transformer_secret"

[staging]
```