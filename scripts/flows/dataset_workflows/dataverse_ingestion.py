from prefect import flow
from prefect.server.schemas.states import Failed, Completed

from tasks.base_tasks import dataverse_metadata_fetcher, dataverse_import, \
    update_publication_date, add_workflow_versioning_url, refine_metadata, \
    enrich_metadata
from utils import generate_dv_flow_run_name


@flow(flow_run_name=generate_dv_flow_run_name)
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

    dataverse_json = refine_metadata(dataverse_json, settings_dict)
    if not dataverse_json:
        return Failed(message='Unable to refine metadata.')

    dataverse_json = add_workflow_versioning_url(dataverse_json, version)
    if not dataverse_json:
        return Failed(message='Unable to store workflow version.')

    dataverse_json = enrich_metadata(dataverse_json, 'elsst/en')
    if not dataverse_json:
        return Failed(message='Unable to enrich metadata using ELSST.')

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
