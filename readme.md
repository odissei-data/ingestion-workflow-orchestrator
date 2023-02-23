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

> You need assign your account the Super User status in order to import via
> the Dataverse API.

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