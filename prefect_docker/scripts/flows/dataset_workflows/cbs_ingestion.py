import jmespath
from prefect import flow
from prefect.orion.schemas.states import Completed, Failed

from queries import CBS_ID_QUERY, DIST_DATE_QUERY
from tasks.base_tasks import xml2json, dataverse_mapper, \
    dataverse_import, update_publication_date, add_workflow_versioning_url, \
    sanitize_emails, semantic_enrichment, refine_metadata


@flow
def cbs_metadata_ingestion(xml_metadata, version, settings_dict):
    """
    Ingestion flow for metadata from CBS.

    :param xml_metadata: xml_metadata of the data provider.
    :param version: dict, contains all version info of the workflow
    :param settings_dict: dict, contains settings for the current workflow
    :return: prefect.orion.schemas.states Failed or Completed
    """
    xml_metadata_sanitized = sanitize_emails(xml_metadata)
    if not xml_metadata_sanitized:
        return Failed(message='Unable to sanitize emails from XML metadata.')

    json_metadata = xml2json(xml_metadata_sanitized)
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

    mapped_metadata = refine_metadata(mapped_metadata, settings_dict)
    if not mapped_metadata:
        return Failed(message='Unable to refine metadata.')

    mapped_metadata = add_workflow_versioning_url(mapped_metadata, version)
    if not mapped_metadata:
        return Failed(message='Unable to store workflow version.')

    # TODO: Add DOI minter step.
    cbs_id = jmespath.search(CBS_ID_QUERY, mapped_metadata)
    doi = 'doi:10.57934/' + cbs_id

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

    enrichment_response = semantic_enrichment(settings_dict, doi)
    if not enrichment_response:
        return Failed(message="Unable to add enrichments.")

    return Completed(message=doi + 'ingested successfully.')
