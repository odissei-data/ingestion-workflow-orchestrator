import copy
from prefect import flow, get_run_logger
from prefect.orion.schemas.states import Failed, Completed

from tasks.base_tasks import xml2json, get_doi_from_header, dataverse_metadata_fetcher, \
    dataverse_import, add_contact_email


@flow
def dataverse_nl_metadata_ingestion(file_path):
    logger = get_run_logger()
    metadata_format = "dataverse_json"
    json_metadata = xml2json(file_path)
    if not json_metadata:
        return Failed(message='Unable to transform from xml to json.')

    doi = get_doi_from_header(json_metadata)
    if not doi:
        return Failed(message='Metadata file contains no DOI in the header.')

    dataverse_json = dataverse_metadata_fetcher(doi, metadata_format)
    if not dataverse_json:
        return Failed(message='Could not fetch dataverse metadata.')

    dataverse_json = add_contact_email(dataverse_json)
    metadata_blocks = copy.deepcopy(
        dataverse_json["datasetVersion"]['metadataBlocks'])
    dataverse_json['datasetVersion'] = {}
    dataverse_json['datasetVersion']['metadataBlocks'] = metadata_blocks
    logger.info(dataverse_json)
    import_response = dataverse_import(dataverse_json)
    if not import_response:
        return Failed(message='Unable to import dataset into Dataverse')

    return Completed(message=file_path + 'ingested successfully.')
