import jmespath
from prefect import flow, get_run_logger
from prefect.orion.schemas.states import Completed, Failed

from queries import CBS_ID_QUERY, DIST_DATE_QUERY
from tasks.base_tasks import xml2json, dataverse_mapper, \
    dataverse_import, update_publication_date, add_workflow_versioning_url, \
    sanitize_emails


@flow
def cbs_metadata_ingestion(xml_metadata, version, settings_dict):
    """
    Ingestion flow for metadata from CBS.

    :param xml_metadata: xml_metadata of the data provider.
    :param version: dict, contains all version info of the workflow
    :param settings_dict: dict, contains settings for the current workflow
    :return: prefect.orion.schemas.states Failed or Completed
    """
    json_metadata = xml2json(xml_metadata)
    if not json_metadata:
        return Failed(message='Unable to transform from xml to json.')

    mapped_metadata = dataverse_mapper(
        json_metadata,
        settings_dict.MAPPING_FILE_PATH,
        settings_dict.TEMPLATE_FILE_PATH,
        False
    )

    if not mapped_metadata:
        return Failed(message='Unable to map metadata.')

    mapped_metadata = add_workflow_versioning_url(mapped_metadata, version)
    if not mapped_metadata:
        return Failed(message='Unable to store workflow version.')

    logger.info(mapped_metadata)

    # TODO: Add DOI minter step.
    cbs_id = jmespath.search(CBS_ID_QUERY, mapped_metadata)
    doi = 'doi:10.57934/' + cbs_id
    logger.info(doi)

    import_response = dataverse_import(mapped_metadata, settings_dict, doi)
    if not import_response:
        return Failed(message='Unable to import dataset into Dataverse.')

    publication_date = jmespath.search(DIST_DATE_QUERY, mapped_metadata)
    if publication_date:
        pub_date_response = update_publication_date(
            publication_date, doi, settings_dict
        )
        if not pub_date_response:
            return Failed(message='Unable to update publication date.')

    return Completed(message=doi + 'ingested successfully.')
