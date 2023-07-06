# Ingestion workflow orchestrator

## Description
This containerized application can be used to run workflows used for ingesting dataset metadata into a Dataverse instance.
The different flows and tasks used in these workflows are created using Prefect. 
If you run the container locally they can be monitored and ran from the Prefect Orion UI at http://localhost:4200.

Most flows start with an entry workflow that can be found in the directory entry_workflows. 
Here the metadata is fetched from an S3 storage, and a version is created. 
A settings dictionary constructed with DynaConf that is specific to the Data Provider is also constructed here.

Next, For every dataset's metadata it runs a sub-flow to handle the actual ingestion.
These flows can be found in the dataset_workflows directory. The dataset workflow uses simple tasks that make an API call to a service. 
These services often transform, improve or alter the metadata in someway.

In short, most ingestion workflows take the following steps:
- Fetch dataset metadata from S3 storage.
- Create version object of all services that will be used for ingestion.
- For every dataset's metadata run dataset workflow.
- Use tasks that make API calls to different services to transform the metadata.



## Services
In this section the different API services used in the workflows are shown. These services can be used in a workflow in different combinations, depending on the metadata provided by the data provider.

| Service Name             | Description                                                                                                                       | Deployment URL                                                                                         | GitHub Repo                                                                               |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| Dataverse Importer       | This service imports metadata into Dataverse.                                                                                     | [https://dataverse-importer.labs.dans.knaw.nl/docs](https://dataverse-importer.labs.dans.knaw.nl/docs) | [GitHub](https://github.com/odissei-data/dataverse-importer)                              |
| Publication Date Updater | Corrects the publication date of the imported metadata.                                                                           | https://dataverse-date-updater.labs.dans.knaw.nl/docs                                                  | [GitHub](https://github.com/odissei-data/publication-date-updater)                        |
| Metadata Fetcher         | Fetches the metadata of a dataset from a Dataverse.                                                                               | https://dataverse-fetcher.labs.dans.knaw.nl/docs                                                       | [GitHub](https://github.com/odissei-data/dataverse-metadata-fetcher)                      |
| Dataverse Mapper         | Maps any JSON to Dataverse's JSON format.                                                                                         | https://dataverse-mapper.labs.dans.knaw.nl/docs                                                        | [GitHub](https://github.com/odissei-data/dataverse-mapper)                                |
| Dans Transformer Service | Transforms from XML to JSON (or from/to other formats).                                                                           | https://transformer.labs.dans.knaw.nl/docs                                                             | [GitHub](https://github.com/ekoi/dans-transformer-service)                                |
| Metadata Refiner         | Refines JSON metadata.                                                                                                            | https://metadata-enhancer.labs.dans.knaw.nl/docs                                                       | [GitHub](https://github.com/odissei-data/metadata-refiner)                                |
| Metadata Enhancer        | Enriches JSON metadata.                                                                                                           | https://metadata-refiner.labs.dans.knaw.nl/docs                                                        | [GitHub](https://github.com/odissei-data/metadata-enhancer)                               |
| Email Sanitizer          | Removes all emails from the metadata.                                                                                             | https://emailsanitizer.labs.dans.knaw.nl/docs                                                          | [GitHub](https://github.com/thomasve-DANS/email-sanitize-microservice)                    |
| Version Tracker          | Stores JSON containing version information.                                                                                       | https://version-tracker.labs.dans.knaw.nl/docs                                                         | [GitHub](https://github.com/odissei-data/version-tracker)                                 |
| DOI Minter               | Mints a DOI for a dataset. Should be used with **CAUTION** since if used with production settings this will mint a permanent DOI. | https://dataciteminter.labs.dans.knaw.nl/docs                                                          | [GitHub](https://github.com/ekoi/submitmd2dc-service/tree/using-dans-transformer-service) |
| Semantic Enrichment      | Enriches the SOLR index with ELSST translations of the keywords from the [ELSST skosmos](https://thesauri.cessda.eu/elsst-3/en/). |                                                                                                        | [GitHub](https://github.com/Dans-labs/semantic-enrichment)                                |


# Development

If you want to develop new flows for the Ingestion Orchestrator you need to set
up your local environment first. Follow the step below, and you should be able
to start development.

First you need to get a couple of containers running. All of these are needed
as they are used by the Ingestion Orchestrator.

### Minio file storage

The metadata that is used by the workflows is stored in s3 buckets. The key, id
and url of the server of the s3 storage should be set in the .secrets.toml as
`AWS_SECRET_ACCESS_KEY`, `AWS_ACCESS_KEY_ID` and `MINIO_SERVER_URL`
respectively.

For a specific data provider a `BUCKET_NAME` should be added for that provider.
The bucket in s3 storage that contains the metadata for the provider should use
the same name as the `BUCKET_NAME` for that provider.

example in odissei_settings.toml:

```
HSN_BUCKET_NAME="hsn-metadata"
```

```
HSN={"ALIAS"="HSN_NL", "BUCKET_NAME"="@format {this.HSN_BUCKET_NAME}", "SOURCE_DATAVERSE_URL"="@format {this.IISG_URL}", "DESTINATION_DATAVERSE_URL"="@format {this.ODISSEI_URL}", "DESTINATION_DATAVERSE_API_KEY"="@format {this.ODISSEI_API_KEY}", "REFINER_ENDPOINT"="@format {this.HSN_REFINER_ENDPOINT}"}
```

In this example, HSN contains all information relating to settings specific to
ingesting the HSN metadata. The BUCKET_NAME set in the HSN dictionary can be
generically used in the code when a bucket name is necessary. It is set to the
HSN_BUCKET_NAME which declares the specific name for the bucket for HSN.
Further explanation on the settings can be found in [Settings files section](#settings-files).

### Dataverse

A local Dataverse instance makes it easy to deposit via the API.

https://github.com/IQSS/dataverse-docker

> Only a Super User can deposit via the API.

Set the `superuser` boolean to true in the `authenticateduser` table. You are
now a Super User.

More information on how to do this can be found in the documentation of the
ODISSEI dataverse stack [here](https://github.com/odissei-data/odissei-stack#becoming-superuser).

### Docker Network

If the containers of the services are setup locally and do not use the
dans-labs services, you need to setup a docker network between the
ingestion-network and the local containers. The commands below should do the
trick.

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
docker network connect ingestion-network semantic-enrichment
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
- semantic-enrichment: 8099

## Dynaconf

The Ingestion Workflow Orchestrator uses Dynaconf to manage its settings. This
chapter will give a very short introduction on Dynaconf. For more information
read the docs.

Use the `.env` file to set the environment to either development, staging or
production. Be careful that setting the env to production will mean that all
flows that use the DOI-minter will be minting persistent DOI's.
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
"BUCKET_NAME" = "@format {this.BUCKET_NAME}"

[development]
"BUCKET_NAME" = "path/to/local/dir"

[production]
"BUCKET_NAME" = "path/to/s3/bucket"
```

## Dataset Workflow Examples

### CBS Metadata Ingestion Workflow

The CBS Metadata Ingestion Workflow is responsible for ingesting metadata from the CBS (Central Bureau of Statistics) data provider into Dataverse. It processes the XML metadata, transforms it into JSON format, maps it to the required format for Dataverse, refines and enriches the metadata, mints a DOI, and finally imports the dataset into Dataverse. The workflow is implemented using Prefect, a workflow management library in Python.

### Workflow Steps

1. **Email Sanitizer**: The XML metadata is passed through the Email Sanitizer service to remove any sensitive email information.

2. **XML to JSON Transformation**: The sanitized XML metadata is transformed into JSON format using the Dans Transformer Service.

3. **Metadata Mapping**: The JSON metadata is mapped to the required format for Dataverse using the Dataverse Mapper service.

4. **Metadata Refinement**: The mapped metadata is refined using the Metadata Refiner service. In CBS's case this means the Alternative Titles and Keywords are improved.

5. **Workflow Versioning**: The workflow versioning URL is added to the metadata using the Version Tracker service. This step ensures that the metadata includes information about the services that processed it.

6. **DOI Minting**: The metadata is passed to the DOI Minter service, which mints a DOI (Digital Object Identifier) for the dataset.

7. **Metadata Enrichment**: The metadata is enriched using two different endpoints of the Metadata Enhancer service. Each service adds specific enrichment to the metadata.

8. **Dataverse Import**: The enriched metadata, along with the DOI, is imported into Dataverse using the Dataverse Importer service.

9. **Publication Date Update**: The publication date is extracted from the metadata using a JMESPath query. If a valid publication date is found, it is passed to the Publication Date Updater service, which updates the publication date of the dataset in Dataverse.

10. **Semantic Enrichment**: The workflow performs semantic enrichment using the Semantic Enrichment service. The enrichment process adds additional information to the SOLR index using ELSST translations of the keywords.

11. **Workflow Completion**: If all the previous steps are completed successfully, the workflow is considered completed, indicating that the dataset has been ingested successfully, including the DOI.

Please note that each service mentioned in the workflow corresponds to the services listed in the table provided earlier.


## Dans Transformer Service

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