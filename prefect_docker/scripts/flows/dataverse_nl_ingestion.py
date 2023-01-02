import copy
import os

from prefect import flow
from prefect.orion.schemas.states import Failed, Completed

from tasks.base_tasks import xml2json, get_doi_from_header, \
    dataverse_metadata_fetcher, \
    dataverse_import, add_contact_email, update_publication_date, \
    add_workflow_versioning_url

DATAVERSE_NL_DATAVERSE_ALIAS = os.getenv('DATAVERSE_NL_DATAVERSE_ALIAS')
DATAVERSE_NL_SOURCE_DATAVERSE_URL = os.getenv(
    'DATAVERSE_NL_SOURCE_DATAVERSE_URL')


@flow
def dataverse_nl_metadata_ingestion(file_path, version):
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
        return {'contact': doi}

    metadata_blocks = copy.deepcopy(
        dataverse_json["datasetVersion"]['metadataBlocks'])
    ds_license = copy.deepcopy(dataverse_json['datasetVersion']['license'])
    dataverse_json['datasetVersion'] = {
        'license': ds_license,
        'metadataBlocks': metadata_blocks
    }

    dataverse_json = add_workflow_versioning_url(dataverse_json, version)
    if not dataverse_json:
        return Failed(message='Unable to store workflow version.')

    import_response = dataverse_import(dataverse_json,
                                       DATAVERSE_NL_DATAVERSE_ALIAS, doi)
    if not import_response:
        return {'import': doi}

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
