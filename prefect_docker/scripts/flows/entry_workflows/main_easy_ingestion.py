import os
import utils
from prefect import flow
from flows.dataset_workflows.easy_ingestion import easy_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning

EASY_METADATA_DIRECTORY = os.getenv('EASY_METADATA_DIRECTORY')
EASY_DATAVERSE_ALIAS = os.getenv('EASY_DATAVERSE_ALIAS')


@flow
def easy_ingestion_pipeline():
    version = create_ingestion_workflow_versioning(transformer=True,
                                                   mapper=True,
                                                   importer=True,
                                                   updater=True)
    utils.workflow_executor(easy_metadata_ingestion, EASY_METADATA_DIRECTORY,
                            version, EASY_DATAVERSE_ALIAS)


if __name__ == "__main__":
    easy_ingestion_pipeline()
