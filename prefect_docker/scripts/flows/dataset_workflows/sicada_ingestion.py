import copy

from prefect import flow
from prefect.orion.schemas.states import Failed, Completed

from tasks.base_tasks import xml2json, get_doi_from_header, \
    dataverse_metadata_fetcher, \
    dataverse_import, add_contact_email, update_publication_date, \
    add_workflow_versioning_url


@flow
def sicada_metadata_ingestion(file_path, version, settings_dict):
    """
    Ingestion flow for metadata from Sicada.

    :param file_path: string, path to xml file
    :param version: dict, contains all version info of the workflow
    :param settings_dict: dict, contains settings for the current workflow
    :return: prefect.orion.schemas.states Failed or Completed
    """
    json_metadata = xml2json(file_path)
    if not json_metadata:
        return Failed(message="Unable to transform from xml to json.")

    doi = get_doi_from_header(json_metadata)
    if not doi:
        return Failed(message="Metadata file contains no DOI in the header.")

    dataverse_json = dataverse_metadata_fetcher(
        "dataverse_json", doi, settings_dict
    )
    if not dataverse_json:
        return Failed(message="Could not fetch dataverse metadata.")

    dataverse_json = add_contact_email(dataverse_json)
    if not dataverse_json:
        return Failed(message="Unable to add contact email")

    dataverse_json = add_workflow_versioning_url(dataverse_json, version)
    if not dataverse_json:
        return Failed(message='Unable to store workflow version.')

    metadata_blocks = copy.deepcopy(
        dataverse_json["datasetVersion"]["metadataBlocks"]
    )
    dataverse_json["datasetVersion"] = {}
    dataverse_json["datasetVersion"]["metadataBlocks"] = metadata_blocks

    try:
        del dataverse_json["metadataLanguage"]
    except Exception:
        pass

    import_response = dataverse_import(
        dataverse_json,
        settings_dict,
        doi
    )

    if not import_response:
        return Failed(message="Unable to import dataset into Dataverse")

    try:
        publication_date = dataverse_json["publicationDate"]
    except KeyError:
        return Failed(message="No date in metadata")

    if publication_date:
        pub_date_response = update_publication_date(
            publication_date, doi, settings_dict
        )

        if not pub_date_response:
            return Failed(message="Unable to update publication date.")

    return Completed(message=file_path + "ingested successfully.")
