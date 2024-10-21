import utils

from prefect import flow
from configuration.config import settings
from flows.dataset_workflows.dataverse_ingestion import \
    dataverse_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning
from tasks.harvest_tasks import oai_harvest_metadata


@flow(name="Dataverse Ingestion Pipeline")
def dataverse_ingestion_pipeline(settings_dict_name: str,
                                 target_url: str = "",
                                 target_key: str = "",
                                 do_harvest: bool = True
                                 ):
    """ Ingestion pipeline dedicated to the Dataverse to Dataverse workflow.

    :param do_harvest: Boolean stating if the dataset metadata should be
     harvested before ingestion.
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

    minio_client = utils.create_s3_client()

    if hasattr(settings_dict,
               'OAI_SET') and settings_dict.OAI_SET and do_harvest:
        oai_harvest_metadata(
            settings.METADATA_PREFIX,
            f'{settings_dict.SOURCE_DATAVERSE_URL}/oai',
            settings_dict.BUCKET_NAME,
            'ListIdentifiers',
            'start_harvest',
            settings_dict.OAI_SET,
            settings_dict.FROM
        )

    elif do_harvest:
        oai_harvest_metadata(
            settings.METADATA_PREFIX,
            f'{settings_dict.SOURCE_DATAVERSE_URL}/oai',
            settings_dict.BUCKET_NAME,
            'ListIdentifiers',
            'start_harvest'
        )

    utils.identifier_list_workflow_executor(
        dataverse_metadata_ingestion,
        settings_dict,
        minio_client,
        "identifiers.json",
        version
    )