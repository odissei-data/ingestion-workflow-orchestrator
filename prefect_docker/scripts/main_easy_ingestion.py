import os
import utils
from prefect import flow
from flows.easy_ingestion import easy_metadata_ingestion

EASY_METADATA_DIRECTORY = os.getenv('EASY_METADATA_DIRECTORY')


@flow
def easy_ingestion_pipeline():
    utils.workflow_executor(easy_metadata_ingestion, EASY_METADATA_DIRECTORY)


if __name__ == "__main__":
    easy_ingestion_pipeline()
