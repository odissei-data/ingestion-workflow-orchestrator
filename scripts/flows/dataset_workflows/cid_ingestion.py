import json
import jmespath
from prefect import flow, get_run_logger
from prefect.server.schemas.states import Completed, Failed

from queries import DIST_DATE_QUERY
from tasks.base_tasks import dataverse_mapper, \
    dataverse_import, update_publication_date, add_workflow_versioning_url, \
    refine_metadata


@flow
async def cid_metadata_ingestion(json_metadata, version, settings_dict):
    """
    Ingestion flow for metadata from CID.

    :param json_metadata: json_metadata of the data provider.
    :param version: dict, contains all version info of the workflow.
    :param settings_dict: dict, contains settings for the current workflow.
    :return: prefect.server.schemas.states Failed or Completed.
    """
    logger = get_run_logger()

    decoded_json = json.loads(json_metadata.decode())
    doi = f"doi:10.73575/{decoded_json['name']}"
    mapped_metadata = await dataverse_mapper(
        decoded_json,
        settings_dict.MAPPING_FILE_PATH,
        settings_dict.TEMPLATE_FILE_PATH,
        False
    )

    if not mapped_metadata:
        return Failed(message='Unable to map metadata')
    mapped_metadata = await refine_metadata(mapped_metadata, settings_dict)
    if not mapped_metadata:
        return Failed(message='Unable to refine metadata.')

    mapped_metadata = add_workflow_versioning_url(mapped_metadata, version)
    if not mapped_metadata:
        return Failed(message='Unable to store workflow version.')
    import_response = await dataverse_import(mapped_metadata, settings_dict,
                                             doi)
    if not import_response:
        return Failed(message='Unable to import dataset into Dataverse')

    publication_date = jmespath.search(DIST_DATE_QUERY, mapped_metadata)
    if publication_date:
        pub_date_response = await update_publication_date(
            publication_date, doi, settings_dict
        )
        if not pub_date_response:
            return Failed(message='Unable to update publication date')

    return Completed(message=doi + " ingested successfully")
