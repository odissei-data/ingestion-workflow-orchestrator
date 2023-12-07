import utils
import boto3

from prefect import flow
from configuration.config import settings
from flows.dataset_workflows.dataverse_ingestion import \
    dataverse_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning
from tasks.harvest_tasks import oai_harvest_metadata


@flow
async def dataverse_ingestion_pipeline(settings_dict_name: str,
                                       target_url: str = None,
                                       target_key: str = None):
    """ Ingestion pipeline dedicated to the Dataverse to Dataverse workflow.

    :param target_url: Optional target dataverse url.
    :param target_key: API key of the optional target dataverse.
    :param settings_dict_name: string, name of the settings you wish to use
    """
    settings_dict = getattr(settings, settings_dict_name)

    if target_url:
        settings_dict.DESTINATION_DATAVERSE_URL = target_url

    if target_key:
        settings_dict.DESTINATION_DATAVERSE_API_KEY = target_key

    version = create_ingestion_workflow_versioning(
        transformer=True,
        fetcher=True,
        refiner=True,
        importer=True,
        updater=True,
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
        oai_harvest_metadata(
            settings.METADATA_PREFIX,
            f'{settings_dict.SOURCE_DATAVERSE_URL}/oai',
            settings_dict.BUCKET_NAME,
            'ListIdentifiers',
            'start_harvest',
            settings_dict.OAI_SET
        )

    else:
        oai_harvest_metadata(
            settings.METADATA_PREFIX,
            f'{settings_dict.SOURCE_DATAVERSE_URL}/oai',
            settings_dict.BUCKET_NAME,
            'ListIdentifiers',
            'start_harvest'
        )

    await utils.identifier_list_workflow_executor(
        dataverse_metadata_ingestion,
        version,
        settings_dict,
        minio_client
    )
