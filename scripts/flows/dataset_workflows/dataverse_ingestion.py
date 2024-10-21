from prefect import flow
from prefect.server.schemas.states import Failed, Completed

from tasks.base_tasks import dataverse_metadata_fetcher, dataverse_import, \
    update_publication_date, add_workflow_versioning_url, refine_metadata, \
    enrich_metadata, dataverse_mapper, dataverse_dataset_check_status, \
    delete_dataset
from utils import generate_dv_flow_run_name, failed_dataverse_ingestion_hook


@flow(flow_run_name=generate_dv_flow_run_name,
      on_failure=[failed_dataverse_ingestion_hook])
def dataverse_metadata_ingestion(pid, version, settings_dict):
    """
    Ingestion flow for Dataverse to dataverse ingestion.

    :param pid: pid of the dataset.
    :param version: dict, contains all version info of the workflow.
    :param settings_dict: dict, contains settings for the current workflow.
    :return: prefect.server.schemas.states Failed or Completed.
    """
    dataverse_json = dataverse_metadata_fetcher(
        "dataverse_json", pid, settings_dict
    )
    if not dataverse_json:
        return Failed(message='Could not fetch dataverse metadata.')

    if hasattr(settings_dict, 'MAPPING_FILE_PATH'):
        dataverse_json = dataverse_mapper(
            dataverse_json,
            settings_dict.MAPPING_FILE_PATH,
            settings_dict.TEMPLATE_FILE_PATH
        )
        if not dataverse_json:
            return Failed(message='Unable to map metadata.')

    dataverse_json = refine_metadata(dataverse_json, settings_dict)
    if not dataverse_json:
        return Failed(message='Unable to refine metadata.')

    dataverse_json = add_workflow_versioning_url(dataverse_json, version)
    if not dataverse_json:
        return Failed(message='Unable to store workflow version.')

    dataverse_json = enrich_metadata(dataverse_json, 'elsst/en')
    if not dataverse_json:
        return Failed(message='Unable to enrich metadata using ELSST.')

    # The result will be 200 (Dataset exists)  or  404 (Dataset does not exist)
    dv_response_status = dataverse_dataset_check_status(
        pid,
        settings_dict.DESTINATION_DATAVERSE_URL
    )

    if not dv_response_status:
        return Failed(message=f'No response from {pid}.')
    if dv_response_status == 200:
        # 200 means that the dataset must be deleted and reingested.
        deleted_response = delete_dataset(pid, settings_dict)
        if not deleted_response:
            return Failed(message=f'Unable to delete dataset: {pid}.')

    import_response = dataverse_import(dataverse_json, settings_dict, pid)
    if not import_response:
        return Failed(message='Unable to import dataset into Dataverse')

    try:
        publication_date = dataverse_json['publicationDate']
    except KeyError:
        return Failed(message="No date in metadata")

    if publication_date:
        pub_date_response = update_publication_date(publication_date, pid,
                                                    settings_dict)
        if not pub_date_response:
            return Failed(message='Unable to update publication date.')

    return Completed(message=pid + 'ingested successfully.')
