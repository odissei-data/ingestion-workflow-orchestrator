import json

import jmespath
from prefect import flow
from prefect.server.schemas.states import Completed, Failed

from queries import DIST_DATE_QUERY
from tasks.base_tasks import dataverse_mapper, \
    dataverse_import, update_publication_date, get_doi_from_dv_json, \
    add_workflow_versioning_url
from utils import is_lower_level_liss_study


@flow
def liss_metadata_ingestion(json_metadata, version, settings_dict):
    """
    Ingestion flow for metadata from LISS.

    :param json_metadata: json_metadata of the data provider.
    :param version: dict, contains all version info of the workflow.
    :param settings_dict: dict, contains settings for the current workflow.
    :return: prefect.orion.schemas.states Failed or Completed.
    """

    decoded_json = json.loads(json_metadata.decode())

    mapped_metadata = dataverse_mapper(
        decoded_json,
        settings_dict.MAPPING_FILE_PATH,
        settings_dict.TEMPLATE_FILE_PATH
    )

    if not mapped_metadata:
        return Failed(message='Unable to map metadata')

    if is_lower_level_liss_study(mapped_metadata)[0]:
        return Completed(message='Lower level LISS study')

    doi = get_doi_from_dv_json(mapped_metadata)
    if not doi:
        return Failed(message='Missing DOI in mapped metadata.')

    mapped_metadata = add_workflow_versioning_url(mapped_metadata, version)
    if not mapped_metadata:
        return Failed(message='Unable to store workflow version.')

    import_response = dataverse_import(mapped_metadata, settings_dict, doi)
    if not import_response:
        return Failed(message='Unable to import dataset into Dataverse')

    publication_date = jmespath.search(DIST_DATE_QUERY, mapped_metadata)
    if publication_date:
        pub_date_response = update_publication_date(
            publication_date, doi, settings_dict
        )
        if not pub_date_response:
            return Failed(message='Unable to update publication date')

    return Completed(message=doi + " ingested successfully")
