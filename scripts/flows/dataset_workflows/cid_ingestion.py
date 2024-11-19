import json
import jmespath

from prefect import flow, get_run_logger
from prefect.states import Completed, Failed
from queries import DIST_DATE_QUERY
from tasks.base_tasks import dataverse_mapper, \
    dataverse_import, update_publication_date, add_workflow_versioning_url, \
    refine_metadata, xml2dvjson, dataverse_dataset_check_status, delete_dataset
from utils import generate_flow_run_name, failed_ingestion_hook


@flow(flow_run_name=generate_flow_run_name, on_failure=[failed_ingestion_hook])
def cid_metadata_ingestion(xml_metadata, version, settings_dict, file_name):
    """
    Ingestion flow for metadata from CID.

    :param file_name: Used in the workflow name and for the on flow fail hook.
    :param json_metadata: json_metadata of the data provider.
    :param version: dict, contains all version info of the workflow.
    :param settings_dict: dict, contains settings for the current workflow.
    :return: prefect.server.schemas.states Failed or Completed.
    """
    logger = get_run_logger()

    json_metadata = xml2dvjson(xml_metadata)
    if not json_metadata:
        return Failed(message='Unable to transform from xml to json.')
    try:
        dv_json = json.loads(json_metadata)
    except json.JSONDecodeError as e:
        return Failed(message='Not valid json metadata')
    doi = dv_json["datasetVersion"]["datasetPersistentId"]
    if not doi:
        return Failed(message='Unable to retrieve dataset doi.')

    dv_response_status = dataverse_dataset_check_status(doi, settings_dict.DESTINATION_DATAVERSE_URL)
    # The result of dv_response status will be 200 (Dataset exists)  or  404 (Dataset does not exist)
    # 403 (deaccession) should never be found in the odissei dataverse

    if not dv_response_status:
        return Failed(message=f'No response from {doi}.')
    if dv_response_status == 200:
        # task_update_dataset(dataverse_json)  # don't update version, but update metadata with new dataverse_json.
        # It means that the dataset must be deleted and reingested.
        deleted_response = delete_dataset(doi, settings_dict)
        if not deleted_response:
            return Failed(message=f'Unable to delete dataset: {doi}.')

    mapped_metadata = add_workflow_versioning_url(dv_json, version)

    if not mapped_metadata:
        return Failed(message='Unable to store workflow version.')
    import_response = dataverse_import(mapped_metadata, settings_dict, f'doi:{doi}' )
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
