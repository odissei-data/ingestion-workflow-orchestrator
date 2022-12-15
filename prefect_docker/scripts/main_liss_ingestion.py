import os
import utils
from prefect import flow
from flows.liss_ingestion import liss_metadata_ingestion

LISS_METADATA_DIRECTORY = os.getenv('LISS_METADATA_DIRECTORY')


@flow
def liss_ingestion_pipeline():
    utils.workflow_executor(liss_metadata_ingestion, LISS_METADATA_DIRECTORY)


if __name__ == "__main__":
    liss_ingestion_pipeline()
