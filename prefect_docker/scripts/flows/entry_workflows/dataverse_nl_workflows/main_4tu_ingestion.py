import os
import utils
from prefect import flow
from flows.dataset_workflows.dataverse_nl_ingestion import \
    dataverse_nl_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning

RESEARCH_DATA_METADATA_DIRECTORY = os.getenv(
    'RESEARCH_DATA_METADATA_DIRECTORY')
RESEARCH_DATA_DATAVERSE_ALIAS = os.getenv('RESEARCH_DATA_DATAVERSE_ALIAS')


@flow
def dataverse_nl_ingestion_pipeline():
    version = create_ingestion_workflow_versioning(transformer=True,
                                                   fetcher=True,
                                                   importer=True,
                                                   updater=True)

    utils.workflow_executor(dataverse_nl_metadata_ingestion,
                            RESEARCH_DATA_METADATA_DIRECTORY, version,
                            RESEARCH_DATA_DATAVERSE_ALIAS)


if __name__ == "__main__":
    dataverse_nl_ingestion_pipeline()
