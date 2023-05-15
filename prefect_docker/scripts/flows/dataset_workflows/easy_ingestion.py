import jmespath
from prefect import flow
from prefect.orion.schemas.states import Completed, Failed

from queries import DIST_DATE_QUERY
from tasks.base_tasks import xml2json, dataverse_mapper, \
    dataverse_import, update_publication_date, get_license, \
    get_doi_from_dv_json, add_workflow_versioning_url


@flow
def easy_metadata_ingestion(xml_metadata, version, settings_dict):
    """
    Ingestion flow for metadata from EASY.

    :param xml_metadata: xml_metadata of the data provider.
    :param version: dict, contains all version info of the workflow
    :param settings_dict: dict, contains settings for the current workflow
    :return: prefect.orion.schemas.states Failed or Completed
    """
    json_metadata = xml2json(xml_metadata)
    if not json_metadata:
        return Failed(message='Unable to transform from xml to json')

    mapped_metadata = dataverse_mapper(
        json_metadata,
        settings_dict.MAPPING_FILE_PATH,
        settings_dict.TEMPLATE_FILE_PATH
    )

    if not mapped_metadata:
        return Failed(message='Unable to map metadata')

    doi = get_doi_from_dv_json(mapped_metadata)
    if not doi:
        return Failed(message='Missing DOI in mapped metadata.')

    dataset_license = get_license(json_metadata)
    mapped_metadata["datasetVersion"]["license"] = dataset_license

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
