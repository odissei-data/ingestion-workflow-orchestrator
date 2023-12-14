import argparse

import boto3
from configuration.config import settings
from prefect import flow
from prefect.deployments.deployments import Deployment
import utils
from flows.dataset_workflows.cbs_ingestion import cbs_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning


@flow
def cbs_ingestion_pipeline(target_url: str = None, target_key: str = None):
    """ Ingestion pipeline dedicated to the CBS metadata ingestion.

    :param target_url: Optional target dataverse url.
    :param target_key: API key of the optional target dataverse.
    """
    settings_dict = settings.CBS

    if target_url:
        settings_dict.DESTINATION_DATAVERSE_URL = target_url

    if target_key:
        settings_dict.DESTINATION_DATAVERSE_API_KEY = target_key

    version = create_ingestion_workflow_versioning(
        transformer=True,
        mapper=True,
        minter=True,
        refiner=True,
        enhancer=True,
        importer=True,
        updater=True,
        settings=settings.CBS
    )

    minio_client = boto3.client(
        's3',
        endpoint_url=settings.MINIO_SERVER_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )

    utils.workflow_executor(
        cbs_metadata_ingestion,
        version,
        settings_dict,
        minio_client
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingestion pipeline for CBS.")
    parser.add_argument('--target_url', type=str, help='Target URL')
    parser.add_argument('--target_key', type=str, help='Target key')
    args = parser.parse_args()

    cbs_ingestion_pipeline(args.target_url, args.target_key)
