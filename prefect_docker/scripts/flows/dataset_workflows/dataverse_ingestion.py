from prefect import flow
from prefect.orion.schemas.states import Failed, Completed

from tasks.base_tasks import xml2json, get_doi_from_header, \
    dataverse_metadata_fetcher, \
    dataverse_import, update_publication_date, add_workflow_versioning_url, \
    refine_metadata


@flow
def dataverse_metadata_ingestion(xml_metadata, version, settings_dict):
    """
    Ingestion flow for Dataverse to dataverse ingestion.

    :param xml_metadata: xml_metadata of the data provider.
    :param version: dict, contains all version info of the workflow
    :param settings_dict: dict, contains settings for the current workflow
    :return: prefect.orion.schemas.states Failed or Completed
    """
    json_metadata = xml2json(xml_metadata)
    if not json_metadata:
        return Failed(message='Unable to transform from xml to json.')

    doi = get_doi_from_header(json_metadata)
    if not doi:
        return Failed(message='Metadata file contains no DOI in the header.')

    dataverse_json = dataverse_metadata_fetcher(
        "dataverse_json", doi, settings_dict
    )
    if not dataverse_json:
        return Failed(message='Could not fetch dataverse metadata.')

    dataverse_json = refine_metadata(dataverse_json, settings_dict)
    if not dataverse_json:
        return Failed(message='Unable to refine metadata.')

    dataverse_json = add_workflow_versioning_url(dataverse_json, version)
    if not dataverse_json:
        return Failed(message='Unable to store workflow version.')

    import_response = dataverse_import(dataverse_json, settings_dict, doi)
    if not import_response:
        return Failed(message='Unable to import dataset into Dataverse')

    try:
        publication_date = dataverse_json['publicationDate']
    except KeyError:
        return Failed(message="No date in metadata")

    if publication_date:
        pub_date_response = update_publication_date(
            publication_date, doi, settings_dict
        )
        if not pub_date_response:
            return Failed(message='Unable to update publication date.')

    return Completed(message=doi + 'ingested successfully.')
