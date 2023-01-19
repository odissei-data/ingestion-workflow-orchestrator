import os
import utils
from prefect import flow, get_run_logger
from flows.liss_ingestion import liss_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning

LISS_METADATA_DIRECTORY = os.getenv('LISS_METADATA_DIRECTORY')


@flow
def liss_ingestion_pipeline():
    version = create_ingestion_workflow_versioning(transformer=True,
                                                   mapper=True,
                                                   importer=True,
                                                   updater=True)
    utils.workflow_executor(liss_metadata_ingestion, LISS_METADATA_DIRECTORY,
                            version)


if __name__ == "__main__":
    liss_ingestion_pipeline()
