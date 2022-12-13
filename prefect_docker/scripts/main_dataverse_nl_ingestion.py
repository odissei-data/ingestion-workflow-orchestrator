import os
import utils
from prefect import flow
from flows.dataverse_nl_ingestion import dataverse_nl_metadata_ingestion

DATAVERSE_NL_METADATA_DIRECTORY = os.getenv('DATAVERSE_NL_METADATA_DIRECTORY')


@flow
def dataverse_nl_ingestion_pipeline():
    utils.workflow_executor(dataverse_nl_metadata_ingestion,
                            DATAVERSE_NL_METADATA_DIRECTORY)


if __name__ == "__main__":
    dataverse_nl_ingestion_pipeline()
