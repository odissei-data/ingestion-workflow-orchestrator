import os
from prefect import flow
from flows.cbs_ingestion import cbs_metadata_ingestion
from flows.dataverse_nl_ingestion import dataverse_nl_metadata_ingestion
from flows.easy_ingestion import easy_metadata_ingestion
from flows.liss_ingestion import liss_metadata_ingestion
from utils import workflow_executor

DATA_PROVIDER = os.getenv('DATA_PROVIDER')


@flow
def ingestion_pipeline():
    metadata_directory = f"/local-metadata/{DATA_PROVIDER}-metadata"
    if DATA_PROVIDER == 'cbs':
        workflow_executor(metadata_directory, cbs_metadata_ingestion)
    elif DATA_PROVIDER == 'easy':
        workflow_executor(metadata_directory, easy_metadata_ingestion)
    elif DATA_PROVIDER == 'liss':
        workflow_executor(metadata_directory, liss_metadata_ingestion)
    elif DATA_PROVIDER == 'dataverse_nl':
        workflow_executor(metadata_directory, dataverse_nl_metadata_ingestion)


if __name__ == "__main__":
    ingestion_pipeline()
