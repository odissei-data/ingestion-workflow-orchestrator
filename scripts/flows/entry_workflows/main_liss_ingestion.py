import utils

from configuration.config import settings
from prefect import flow
from flows.dataset_workflows.liss_ingestion import liss_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning
from tasks.harvest_tasks import harvest_metadata, \
    get_most_recent_publication_date


@flow
def liss_ingestion_pipeline(target_url: str = "", 
                            target_key: str = "",
                            target_bucket: str = "",
                            do_harvest: bool = True,
                            full_harvest: bool = False
                            ):
    """ Ingestion pipeline dedicated to the LISS metadata ingestion.
    :param full_harvest: Boolean stating if a full harvest should be performed.
    :param do_harvest: Boolean stating if the dataset metadata should be
     harvested before ingestion.
    :param target_bucket: Optional target S3 bucket name.
    :param target_url: Optional target dataverse url.
    :param target_key: API key of the optional target dataverse.
    """
    settings_dict = settings.LISS

    if target_url:
        settings_dict.DESTINATION_DATAVERSE_URL = target_url

    if target_key:
        settings_dict.DESTINATION_DATAVERSE_API_KEY = target_key

    if target_bucket:
        settings_dict.BUCKET_NAME = target_bucket

    version = create_ingestion_workflow_versioning(
        transformer=True,
        mapper=True,
    )

    s3_client = utils.create_s3_client()

    if do_harvest:
        if full_harvest:
            timestamp = None
        else:
            timestamp = get_most_recent_publication_date(settings_dict)

        harvest_metadata(
            settings_dict.BUCKET_NAME,
            "start_liss_harvest",
            timestamp if timestamp else None
        )

    utils.workflow_executor(
        liss_metadata_ingestion,
        version,
        settings_dict,
        s3_client
    )
