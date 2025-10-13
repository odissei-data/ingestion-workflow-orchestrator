import utils

from configuration.config import settings
from prefect import flow
from flows.dataset_workflows.cbs_ingestion import cbs_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning


@flow
def cbs_ingestion_pipeline(target_url: str = "", 
                           target_key: str = "",
                           target_bucket: str = "",
                           do_harvest: bool=False,
                           full_harvest: bool=False
                           ):
    """ Ingestion pipeline dedicated to the CBS metadata ingestion.

    :param full_harvest: Boolean stating if a full harvest should be performed. 
     Not used for CBS yet.
    :param do_harvest: Boolean stating if the dataset metadata should be
     harvested before ingestion. Not used for CBS yet.
    :param target_bucket: Optional target S3 bucket name.
    :param target_url: Optional target dataverse url.
    :param target_key: API key of the optional target dataverse.
    """
    settings_dict = settings.CBS

    if target_url:
        settings_dict.DESTINATION_DATAVERSE_URL = target_url

    if target_key:
        settings_dict.DESTINATION_DATAVERSE_API_KEY = target_key

    if target_bucket:
        settings_dict.BUCKET_NAME = target_bucket

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

    s3_client = utils.create_s3_client()

    utils.workflow_executor(
        cbs_metadata_ingestion,
        version,
        settings_dict,
        s3_client
    )
