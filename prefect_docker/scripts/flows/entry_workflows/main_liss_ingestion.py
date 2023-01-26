import os
import utils
from prefect import flow
from flows.dataset_workflows.liss_ingestion import liss_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning

LISS_METADATA_DIRECTORY = os.getenv('LISS_METADATA_DIRECTORY')
LISS_DATAVERSE_ALIAS = os.getenv('LISS_DATAVERSE_ALIAS')


@flow
def liss_ingestion_pipeline():
    version = create_ingestion_workflow_versioning(transformer=True,
                                                   mapper=True,
                                                   importer=True,
                                                   updater=True)
    utils.workflow_executor(liss_metadata_ingestion, LISS_METADATA_DIRECTORY,
                            version, LISS_DATAVERSE_ALIAS)


if __name__ == "__main__":
    liss_ingestion_pipeline()
