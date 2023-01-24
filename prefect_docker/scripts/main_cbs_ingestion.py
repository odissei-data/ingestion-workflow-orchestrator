import os
from prefect import flow, get_run_logger

import utils
from flows.cbs_ingestion import cbs_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning

CBS_METADATA_DIRECTORY = os.getenv('CBS_METADATA_DIRECTORY')


@flow
def cbs_ingestion_pipeline():
    version = create_ingestion_workflow_versioning(transformer=True,
                                                   mapper=True,
                                                   minter=True,
                                                   importer=True,
                                                   updater=True)
    utils.workflow_executor(cbs_metadata_ingestion, CBS_METADATA_DIRECTORY,
                            version)


if __name__ == "__main__":
    cbs_ingestion_pipeline()
