import json

import jmespath
from prefect import flow
from prefect.states import Completed, Failed

from queries import DIST_DATE_QUERY
from tasks.base_tasks import dataverse_mapper, \
    dataverse_import, update_publication_date, get_doi_from_dv_json, \
    add_workflow_versioning_url, enrich_metadata, refine_metadata, \
    dataverse_dataset_check_status, delete_dataset
from utils import is_lower_level_liss_study, generate_flow_run_name, \
    failed_ingestion_hook


@flow(flow_run_name=generate_flow_run_name, on_failure=[failed_ingestion_hook])
def liss_metadata_ingestion(json_metadata, version, settings_dict, file_name):
    """
    Ingestion flow for metadata from LISS.

    :param file_name: Used in the workflow name and for the on flow fail hook.
    :param json_metadata: json_metadata of the data provider.
    :param version: dict, contains all version info of the workflow.
    :param settings_dict: dict, contains settings for the current workflow.
    :return: prefect.server.schemas.states Failed or Completed.
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

    mapped_metadata = refine_metadata(mapped_metadata, settings_dict)
    if not mapped_metadata:
        return Failed(message='Unable to refine metadata.')

    mapped_metadata = add_workflow_versioning_url(mapped_metadata, version)
    if not mapped_metadata:
        return Failed(message='Unable to store workflow version.')

    mapped_metadata = enrich_metadata(mapped_metadata, 'elsst/en')
    if not mapped_metadata:
        return Failed(message='Unable to enrich metadata using ELSST.')

    # The result will be 200 (Dataset exists)  or  404 (Dataset does not exist)
    dv_response_status = dataverse_dataset_check_status(
        doi,
        settings_dict.DESTINATION_DATAVERSE_URL
    )

    if not dv_response_status:
        return Failed(message=f'No response from {doi}.')
    if dv_response_status == 200:
        # 200 means that the dataset must be deleted and reingested.
        deleted_response = delete_dataset(doi, settings_dict)
        if not deleted_response:
            return Failed(message=f'Unable to delete dataset: {doi}.')

    import_response = dataverse_import(mapped_metadata, settings_dict, doi)
    if not import_response:
        return Failed(message='Unable to import dataset into Dataverse')

    try:
        publication_date = jmespath.search(DIST_DATE_QUERY, mapped_metadata)
    except KeyError:
        return Failed(message="No date in metadata")

    if publication_date:
        pub_date_response = update_publication_date(publication_date, doi,
                                                    settings_dict)
        if not pub_date_response:
            return Failed(message='Unable to update publication date.')

    return Completed(message=doi + " ingested successfully")

