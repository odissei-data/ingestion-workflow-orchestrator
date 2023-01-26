import os
import utils
from prefect import flow
from flows.dataset_workflows.dataverse_nl_ingestion import dataverse_nl_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning

DATAVERSE_NL_METADATA_DIRECTORY = os.getenv('DATAVERSE_NL_METADATA_DIRECTORY')
DATAVERSE_NL_DATAVERSE_ALIAS = os.getenv('DATAVERSE_NL_DATAVERSE_ALIAS')


@flow
def dataverse_nl_ingestion_pipeline():
    version = create_ingestion_workflow_versioning(transformer=True,
                                                   fetcher=True,
                                                   importer=True,
                                                   updater=True)

    utils.workflow_executor(dataverse_nl_metadata_ingestion,
                            DATAVERSE_NL_METADATA_DIRECTORY, version)


if __name__ == "__main__":
    dataverse_nl_ingestion_pipeline()
