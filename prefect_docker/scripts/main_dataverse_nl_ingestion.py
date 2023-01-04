import os
import utils
from prefect import flow
from flows.dataverse_nl_ingestion import dataverse_nl_metadata_ingestion

DATAVERSE_NL_METADATA_DIRECTORY = os.getenv('DATAVERSE_NL_METADATA_DIRECTORY')


@flow
def dataverse_nl_ingestion_pipeline():
    for sub_dir in os.listdir(DATAVERSE_NL_METADATA_DIRECTORY):
        metadata_dir = os.path.join(DATAVERSE_NL_METADATA_DIRECTORY, sub_dir)
        if os.path.isdir(metadata_dir):
            utils.workflow_executor(dataverse_nl_metadata_ingestion,
                                    metadata_dir)


if __name__ == "__main__":
    dataverse_nl_ingestion_pipeline()
