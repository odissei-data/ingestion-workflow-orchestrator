import asyncio

import boto3
import utils

from configuration.config import settings
from prefect import flow
from flows.dataset_workflows.liss_ingestion import liss_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning
from tasks.harvest_tasks import harvest_metadata


@flow
async def liss_ingestion_pipeline(target_url: str = None,
                                  target_key: str = None):
    """ Ingestion pipeline dedicated to the LISS metadata ingestion.

    :param target_url: Optional target dataverse url.
    :param target_key: API key of the optional target dataverse.
    """
    settings_dict = settings.LISS

    if target_url:
        settings_dict.DESTINATION_DATAVERSE_URL = target_url

    if target_key:
        settings_dict.DESTINATION_DATAVERSE_API_KEY = target_key

    version = create_ingestion_workflow_versioning(
        transformer=True,
        mapper=True,
        importer=True,
        updater=True
    )

    minio_client = boto3.client(
        's3',
        endpoint_url=settings.MINIO_SERVER_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )

    harvest_metadata(
        settings_dict.BUCKET_NAME,
        "start_liss_harvest"
    )

    await utils.workflow_executor(
        liss_metadata_ingestion,
        version,
        settings_dict,
        minio_client
    )
