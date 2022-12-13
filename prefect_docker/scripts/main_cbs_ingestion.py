import os
import utils
from prefect import flow
from flows.cbs_ingestion import cbs_metadata_ingestion

CBS_METADATA_DIRECTORY = os.getenv('CBS_METADATA_DIRECTORY')


@flow
def cbs_ingestion_pipeline():
    utils.workflow_executor(cbs_metadata_ingestion, CBS_METADATA_DIRECTORY)


if __name__ == "__main__":
    cbs_ingestion_pipeline()
