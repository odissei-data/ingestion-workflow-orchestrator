import copy
import os

from prefect import flow, get_run_logger
from prefect.orion.schemas.states import Failed, Completed

from tasks.base_tasks import xml2json, get_doi_from_header, \
    dataverse_metadata_fetcher, \
    dataverse_import, add_contact_email, update_publication_date

IISG_SOURCE_DATAVERSE_URL = os.getenv('IISG_SOURCE_DATAVERSE_URL')


@flow
def iisg_metadata_ingestion(file_path, alias, version):
    logger = get_run_logger()

    metadata_format = "dataverse_json"
    json_metadata = xml2json(file_path)
    if not json_metadata:
        return Failed(message='Unable to transform from xml to json.')

    doi = get_doi_from_header(json_metadata)
    if not doi:
        return Failed(message='Metadata file contains no DOI in the header.')

    dataverse_json = dataverse_metadata_fetcher(
        doi,
        IISG_SOURCE_DATAVERSE_URL,
        metadata_format,
    )
    if not dataverse_json:
        return Failed(message='Could not fetch dataverse metadata.')

    dataverse_json = add_contact_email(dataverse_json)
    if not dataverse_json:
        return Failed(message='Unable to add contact email')


    metadata_blocks = copy.deepcopy(
        dataverse_json["datasetVersion"]['metadataBlocks']
    )
    dataverse_json['datasetVersion'] = {}
    dataverse_json['datasetVersion']['metadataBlocks'] = metadata_blocks

    logger.info(dataverse_json)

    import_response = dataverse_import(
        dataverse_json,
        alias,
        doi
    )

    if not import_response:
        return Failed(message='Unable to import dataset into Dataverse')

    try:
        publication_date = dataverse_json['publicationDate']
    except KeyError:
        return Failed(message="No date in metadata")

    if publication_date:
        pub_date_response = update_publication_date(publication_date, doi)

        if not pub_date_response:
            return Failed(message='Unable to update publication date.')

    return Completed(message=file_path + 'ingested successfully.')
