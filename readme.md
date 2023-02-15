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

Fetches the metadata of a dataset from a dataverse.

https://github.com/odissei-data/dataverse-metadata-fetcher

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
```

### Ports
The containers are assumed to be running on the following ports. If needed,
adjust the port numbers in the `.env` file.

- dataverse: 8080
- dataverse-importer: 8091
- metadata-fetcher: 8092
- publication-date-update: 8093
