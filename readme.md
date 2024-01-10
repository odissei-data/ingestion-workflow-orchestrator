# Ingestion workflow orchestrator

## Description

This containerized application can be used to run workflows used for ingesting
dataset metadata into a Dataverse instance. The different flows and tasks used
in these workflows are created using Prefect. If you run the container locally
they can be monitored and ran from the Prefect Orion UI
at http://localhost:4200.

Most flows start with an entry workflow that can be found in the directory
entry_workflows. Here the metadata is first harvested using OAI-PMH and
uploaded to S3 storage. After, the metadata is fetched from that S3 storage,
and a provenance object is created for the ingested metadata. A settings
dictionary constructed with DynaConf that is specific to the Data Provider is
also constructed here.

Next, For every dataset's metadata it runs a sub-flow to handle the actual
ingestion. These flows can be found in the dataset_workflows directory. The
dataset workflow uses simple tasks that make an API call to a service. These
services often transform, improve or alter the metadata in some way.

In short, most ingestion workflows take the following steps:

- Harvest metadata and upload it to S3 storage.
- Fetch dataset metadata from S3 storage.
- Create version object of all services that will be used for ingestion.
- For every dataset's metadata run dataset workflow.
- Use tasks that make API calls to different services to transform the
  metadata.

## Services

In this section the different API services used in the workflows are shown.
These services can be used in a workflow in different combinations, depending
on the metadata provided by the data provider.

| Service Name             | Description                                                                                                                       | Deployment URL                                                                                         | GitHub Repo                                                                               |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| Dataverse Importer       | This service imports metadata into Dataverse.                                                                                     | [https://dataverse-importer.labs.dansdemo.nl/docs](https://dataverse-importer.labs.dansdemo.nl/docs) | [GitHub](https://github.com/odissei-data/dataverse-importer)                              |
| Publication Date Updater | Corrects the publication date of the imported metadata.                                                                           | https://dataverse-date-updater.labs.dansdemo.nl/docs                                                  | [GitHub](https://github.com/odissei-data/publication-date-updater)                        |
| Metadata Fetcher         | Fetches the metadata of a dataset from a Dataverse.                                                                               | https://dataverse-fetcher.labs.dansdemo.nl/docs                                                       | [GitHub](https://github.com/odissei-data/dataverse-metadata-fetcher)                      |
| Dataverse Mapper         | Maps any JSON to Dataverse's JSON format.                                                                                         | https://dataverse-mapper.labs.dansdemo.nl/docs                                                        | [GitHub](https://github.com/odissei-data/dataverse-mapper)                                |
| Dans Transformer Service | Transforms from XML to JSON (or from/to other formats).                                                                           | https://transformer.labs.dansdemo.nl/docs                                                             | [GitHub](https://github.com/ekoi/dans-transformer-service)                                |
| Metadata Refiner         | Refines JSON metadata.                                                                                                            | https://metadata-enhancer.labs.dansdemo.nl/docs                                                       | [GitHub](https://github.com/odissei-data/metadata-refiner)                                |
| Metadata Enhancer        | Enriches JSON metadata.                                                                                                           | https://metadata-refiner.labs.dansdemo.nl/docs                                                        | [GitHub](https://github.com/odissei-data/metadata-enhancer)                               |
| Email Sanitizer          | Removes all emails from the metadata.                                                                                             | https://emailsanitizer.labs.dansdemo.nl/docs                                                          | [GitHub](https://github.com/thomasve-DANS/email-sanitize-microservice)                    |
| Version Tracker          | Stores JSON containing version information.                                                                                       | https://version-tracker.labs.dansdemo.nl/docs                                                         | [GitHub](https://github.com/odissei-data/version-tracker)                                 |
| DOI Minter               | Mints a DOI for a dataset. Should be used with **
CAUTION** since if used with production settings this will mint a permanent DOI. | https://dataciteminter.labs.dansdemo.nl/docs                                                          | [GitHub](https://github.com/ekoi/submitmd2dc-service/tree/using-dans-transformer-service) |
| Semantic Enrichment      | Enriches the SOLR index with ELSST translations of the keywords from the [ELSST skosmos](https://thesauri.cessda.eu/elsst-3/en/). |                                                                                                        | [GitHub](https://github.com/Dans-labs/semantic-enrichment)                                |
| OAI-PMH Harvester        | Harvester service to harvest the metadata from data providers using OAI-PMH.                                                      |                                                                                                        | [GitHub](https://github.com/odissei-data/odissei-harvester)                               |

# Development

## Available Make commands

Here is a set list of make command that can be used for easy setup:

- `make build`: Build and start the project.
- `make start`: Start the project in non-detached mode.
- `make startbg`: Start the project in detached mode (background).
- `make down`: Down the running project.
- `make dev-build`: Build and start the development setup.
- `make dev-down`: Down the ingest services in development mode.
- `make ingest`: Run a specific ingest flow in Prefect with optional arguments
  for the target.
- `make deploy`: Deploy all ingestion workflows to the Prefect server.

## Project setup 
### Development setup
If you want to develop new flows for the Ingestion Orchestrator you might want
to run the services described above locally. This is possible by following the
steps:

1. `cp dot_env_example .env`
2. `cp scripts/configuration/secrets_example.toml scripts/configuration/.secrets.toml`
3. Add the necessary API tokens and credentials to the .secrets.toml
4. set `ENV_FOR_DYNACONF` in the .env to `development`
5. `make dev-build`
   This should set up the prefect container and the services used during the
   ingestion workflows.

### Staging setup
1. `cp dot_env_example .env`
2. `cp scripts/configuration/secrets_example.toml scripts/configuration/.secrets.toml`
3. Add the necessary API tokens and credentials to the .secrets.toml
4. set `ENV_FOR_DYNACONF` in the .env to `staging`
5. `make build`

### Running an ingestion via deploy

1. `make deploy`
2. Go to localhost:4200/deployments
3. Click the ellipsis icon of a workflow and select either **custom run** or **
   quick run**

If you've selected **custom run** you can optionally fill in a target url and
key argument to specify a different target Dataverse. If you select **quick
run** it will use the target in the settings in odissei_settings.toml and the
key in .secrets.toml.

For the Dataverse ingestion pipeline, there is also a required argument for
the `settings_dict_name`. The options for ingesting with Dataverse as both the
source and target use the following input:

DANS datastation SSH, subset of only the social science datasets:
`'DANS'`

IISG's datasets: `'HSN'`

Subverses of dataverse.nl:
`'TWENTE'`, `'DELFT'`, `'AVANS'`, `'FONTYS'`, `'GRONINGEN'`, `'HANZE'`, `'HR'`
, `'LEIDEN'`, `'MAASTRICHT'`, `'TILBURG'`, `'TRIMBOS'`, `'UMCU'`, `'UTRECHT'`
, `'VU'`

### Running an ingestion via the command line

1. `make ingest data_provider=CBS TARGET_URL=https://portal.example.odissei.nl TARGET_KEY=abcde123-11aa-22bb-3c4d-098765432abc`
2. A prompt will show confirming the target
3. Type yes to continue or anything else to abort.

The `make ingest` command allows you to specify the url and API key of a
specific target Dataverse. If you do not provide them, it will use the target
in the settings in odissei_settings.toml and the key in .secrets.toml.

This is the list of data providers that can be used in the `make ingest` command:

`'TWENTE'`, `'DELFT'`, `'AVANS'`, `'FONTYS'`, `'GRONINGEN'`, `'HANZE'`, `'HR'`, `'LEIDEN'`, `'MAASTRICHT'`, `'TILBURG'`, `'TRIMBOS'`, `'UMCU'`, `'UTRECHT'`, `'VU'`, `'DANS'`, `'CBS'`, `'LISS'`, `'HSN'`, `'CID'`


## Minio file storage

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
Further explanation on the settings can be found
in [Settings files section](#settings-files).

### Dataverse

A local Dataverse instance makes it easy to deposit via the API.

https://github.com/IQSS/dataverse-docker

> Only a Super User can deposit via the API.

Set the `superuser` boolean to true in the `authenticateduser` table. You are
now a Super User.

More information on how to do this can be found in the documentation of the
ODISSEI dataverse
stack [here](https://github.com/odissei-data/odissei-stack#becoming-superuser).

If you use a containerized Dataverse instance it should live in the same
network as the dev services.

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

The CBS Metadata Ingestion Workflow is responsible for ingesting metadata from
the CBS (Central Bureau of Statistics) data provider into Dataverse. It
processes the XML metadata, transforms it into JSON format, maps it to the
required format for Dataverse, refines and enriches the metadata, mints a DOI,
and finally imports the dataset into Dataverse. The workflow is implemented
using Prefect, a workflow management library in Python.

### Workflow Steps

1. **Email Sanitizer**: The XML metadata is passed through the Email Sanitizer
   service to remove any sensitive email information.

2. **XML to JSON Transformation**: The sanitized XML metadata is transformed
   into JSON format using the Dans Transformer Service.

3. **Metadata Mapping**: The JSON metadata is mapped to the required format for
   Dataverse using the Dataverse Mapper service.

4. **Metadata Refinement**: The mapped metadata is refined using the Metadata
   Refiner service. In CBS's case this means the Alternative Titles and
   Keywords are improved.

5. **Workflow Versioning**: The workflow versioning URL is added to the
   metadata using the Version Tracker service. This step ensures that the
   metadata includes information about the services that processed it.

6. **DOI Minting**: The metadata is passed to the DOI Minter service, which
   mints a DOI (Digital Object Identifier) for the dataset.

7. **Metadata Enrichment**: The metadata is enriched using two different
   endpoints of the Metadata Enhancer service. Each service adds specific
   enrichment to the metadata.

8. **Dataverse Import**: The enriched metadata, along with the DOI, is imported
   into Dataverse using the Dataverse Importer service.

9. **Publication Date Update**: The publication date is extracted from the
   metadata using a JMESPath query. If a valid publication date is found, it is
   passed to the Publication Date Updater service, which updates the
   publication date of the dataset in Dataverse.

10. **Semantic Enrichment**: The workflow performs semantic enrichment using
    the Semantic Enrichment service. The enrichment process adds additional
    information to the SOLR index using ELSST translations of the keywords.

11. **Workflow Completion**: If all the previous steps are completed
    successfully, the workflow is considered completed, indicating that the
    dataset has been ingested successfully, including the DOI.

Please note that each service mentioned in the workflow corresponds to the
services listed in the table provided earlier.
