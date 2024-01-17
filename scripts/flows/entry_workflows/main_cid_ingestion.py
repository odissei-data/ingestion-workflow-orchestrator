import utils

from prefect import flow
from configuration.config import settings
from flows.dataset_workflows.cid_ingestion import cid_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning
from tasks.harvest_tasks import harvest_metadata


@flow
def cid_ingestion_pipeline(target_url: str = None, target_key: str = None,
                           do_harvest: bool = True):
    """ Ingestion pipeline dedicated to the CID metadata ingestion.

    :param do_harvest: Boolean stating if the dataset metadata should be
     harvested before ingestion.
    :param target_url: Optional target dataverse url.
    :param target_key: API key of the optional target dataverse.
    """
    settings_dict = settings.CID

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

    if do_harvest:
        harvest_metadata(
            settings_dict.BUCKET_NAME,
            "start_cid_harvest"
        )

    s3_client = utils.create_s3_client()

    utils.workflow_executor(
        cid_metadata_ingestion,
        version,
        settings_dict,
        s3_client
    )
