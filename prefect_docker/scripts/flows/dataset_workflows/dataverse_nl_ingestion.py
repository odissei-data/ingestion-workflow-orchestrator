import copy
import os

from prefect import flow, get_run_logger
from prefect.orion.schemas.states import Failed, Completed

from tasks.base_tasks import xml2json, get_doi_from_header, \
    dataverse_metadata_fetcher, \
    dataverse_import, add_contact_email, update_publication_date, \
    format_license, add_workflow_versioning_url

DATAVERSE_NL_SOURCE_DATAVERSE_URL = os.getenv(
    'DATAVERSE_NL_SOURCE_DATAVERSE_URL')


@flow
def dataverse_nl_metadata_ingestion(file_path, alias, version):
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
        DATAVERSE_NL_SOURCE_DATAVERSE_URL,
        metadata_format,
    )
    if not dataverse_json:
        return Failed(message='Could not fetch dataverse metadata.')

    dataverse_json = add_contact_email(dataverse_json)
    if not dataverse_json:
        return Failed(message='Unable to add contact email')
    logger.info(dataverse_json)

    metadata_blocks = copy.deepcopy(
        dataverse_json["datasetVersion"]['metadataBlocks'])

    terms_of_use = None
    if 'termsOfUse' in dataverse_json['datasetVersion']:
        terms_of_use = copy.deepcopy(
            dataverse_json['datasetVersion']['termsOfUse'])

    ds_license = None
    if 'license' in dataverse_json['datasetVersion']:
        ds_license = copy.deepcopy(dataverse_json['datasetVersion']['license'])

    dataverse_json['datasetVersion'] = {
        'metadataBlocks': metadata_blocks
    }

    if terms_of_use:
        dataverse_json['datasetVersion']['termsOfUse'] = terms_of_use

    logger.info(ds_license)
    if ds_license and ds_license != 'NONE':
        dataverse_json['datasetVersion']['license'] = format_license(
            ds_license)

    dataverse_json = add_workflow_versioning_url(dataverse_json, version)
    if not dataverse_json:
        return Failed(message='Unable to store workflow version.')

    import_response = dataverse_import(dataverse_json,
                                       alias, doi)
    if not import_response:
        return Failed(message='Unable to import dataset into Dataverse')

    try:
        publication_date = dataverse_json['publicationDate']
    except KeyError:
        return Failed(message="No date in metadata")

    if publication_date:
        pub_date_response = update_publication_date(publication_date,
                                                    doi)
        if not pub_date_response:
            return Failed(message='Unable to update publication date.')

    return Completed(message=file_path + 'ingested successfully.')
