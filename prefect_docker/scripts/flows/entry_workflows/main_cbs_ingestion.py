import os
from prefect import flow
import utils
from flows.dataset_workflows.cbs_ingestion import cbs_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning

CBS_METADATA_DIRECTORY = os.getenv('CBS_METADATA_DIRECTORY')
CBS_DATAVERSE_ALIAS = os.getenv('CBS_DATAVERSE_ALIAS')

@flow
def cbs_ingestion_pipeline():
    version = create_ingestion_workflow_versioning(transformer=True,
                                                   mapper=True,
                                                   minter=True,
                                                   importer=True,
                                                   updater=True)
    utils.workflow_executor(cbs_metadata_ingestion, CBS_METADATA_DIRECTORY,
                            version, CBS_DATAVERSE_ALIAS)


if __name__ == "__main__":
    cbs_ingestion_pipeline()
