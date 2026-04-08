import utils

from prefect import flow
from configuration.config import settings
from flows.dataset_workflows.cid_ingestion import cid_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning
from tasks.harvest_tasks import oai_harvest_metadata, \
    get_most_recent_publication_date


@flow(name="CID Ingestion Pipeline")
def cid_ingestion_pipeline(target_url: str = "", 
                           target_key: str = "",
                           target_bucket: str = "",
                           do_harvest: bool = True,
                           full_harvest: bool = False
                           ):
    """ Ingestion pipeline dedicated to the CID metadata ingestion.

    :param full_harvest: Boolean stating if a full harvest should be performed.
    :param do_harvest: Boolean stating if the dataset metadata should be
     harvested before ingestion.
    :param target_bucket: Optional target MinIO bucket name.
    :param target_url: Optional target dataverse url.
    :param target_key: API key of the optional target dataverse.
    """
    settings_dict = settings.CID

    if target_url:
        settings_dict.DESTINATION_DATAVERSE_URL = target_url

    if target_key:
        settings_dict.DESTINATION_DATAVERSE_API_KEY = target_key

    if target_bucket:
        settings_dict.BUCKET_NAME = target_bucket
 
    version = create_ingestion_workflow_versioning(
        transformer=True,
        refiner=False,
        settings=settings_dict
    )

    minio_client = utils.create_minio_client()

    if do_harvest:
        if full_harvest:
            timestamp = None
        else:
            timestamp = get_most_recent_publication_date(settings_dict)

        harvest_params = {
            'metadata_prefix': settings.CID_METADATA_PREFIX,
            'oai_endpoint': f'{settings_dict.SOURCE_DATAVERSE_URL}/oai',
            'bucket_name': settings_dict.BUCKET_NAME,
            'verb': 'ListRecords',
            'harvester_endpoint': 'start_harvest'
        }

        if hasattr(settings_dict, 'OAI_SET') and settings_dict.OAI_SET:
            harvest_params['oai_set'] = settings_dict.OAI_SET

        if timestamp:
            harvest_params['timestamp'] = timestamp

        oai_harvest_metadata(**harvest_params)

    utils.workflow_executor(
        cid_metadata_ingestion,
        version,
        settings_dict,
        minio_client
    )
