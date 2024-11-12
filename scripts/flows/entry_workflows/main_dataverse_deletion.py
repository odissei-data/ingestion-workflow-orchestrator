from prefect import flow

import utils
from configuration.config import settings
from flows.dataset_workflows.dataverse_deletion import dataverse_metadata_deletion
from tasks.harvest_tasks import oai_harvest_metadata, \
    get_most_recent_publication_date


@flow(name="Dataverse Deleted Pipeline")
def dataverse_deletion_pipeline(settings_dict_name: str,
                                target_url: str = "",
                                target_key: str = "",
                                do_harvest: bool = True
                                ):
    """ Deletion pipeline dedicated to the Dataverse to Dataverse workflow.

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


    minio_client = utils.create_s3_client()

    if do_harvest:
        timestamp = get_most_recent_publication_date(settings_dict)
        oai_harvest_metadata(
            settings.METADATA_PREFIX,
            f'{settings_dict.SOURCE_DATAVERSE_URL}/oai',
            settings_dict.BUCKET_NAME,
            'ListIdentifiers',
            'start_harvest',
            settings_dict.OAI_SET if settings_dict.OAI_SET else None,
            timestamp if timestamp else None
        )

    utils.identifier_list_workflow_executor(
        dataverse_metadata_deletion,
        settings_dict,
        minio_client,
        "identifiers-deleted.json",
    )
