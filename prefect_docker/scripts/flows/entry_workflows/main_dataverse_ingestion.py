import argparse

import boto3
from prefect import flow

from configuration.config import settings
from flows.dataset_workflows.dataverse_ingestion import \
    dataverse_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning
import utils
from tasks.harvest_tasks import harvest_metadata


@flow
def dataverse_ingestion_pipeline(settings_dict_name):
    """
    Ingestion pipeline dedicated to the Dataverse to Dataverse workflow.

    :param settings_dict_name: string, name of the settings you wish to use
    :return: None
    """
    settings_dict = getattr(settings, settings_dict_name)

    version = create_ingestion_workflow_versioning(
        transformer=True,
        fetcher=True,
        importer=True,
        updater=True,
        refiner=True,
        settings=settings_dict
    )

    minio_client = boto3.client(
        's3',
        endpoint_url=settings.MINIO_SERVER_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )

    # Check if settings_dict.OAI_SET is not null or empty
    if hasattr(settings_dict, 'OAI_SET') and settings_dict.OAI_SET:
        harvest_metadata(
            settings.METADATA_PREFIX,
            f'{settings_dict.SOURCE_DATAVERSE_URL}/oai',
            settings_dict.BUCKET_NAME,
            'ListIdentifiers',
            'start_harvest',
            settings_dict.OAI_SET
        )

    else:
        harvest_metadata(
            settings.METADATA_PREFIX,
            f'{settings_dict.SOURCE_DATAVERSE_URL}/oai',
            settings_dict.BUCKET_NAME,
            'ListIdentifiers',
            'start_harvest'
        )

    utils.identifier_list_workflow_executor(
        dataverse_metadata_ingestion,
        version,
        settings_dict,
        minio_client
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingestion pipeline for Dataverse2Dataverse workflow.")
    parser.add_argument("settings_dict_name",
                        help="Name of the target subverse.")
    args = parser.parse_args()

    dataverse_ingestion_pipeline(args.settings_dict_name)
