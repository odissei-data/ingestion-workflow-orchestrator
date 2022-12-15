import os

from prefect import flow
from prefect.orion.schemas.states import Completed, Failed
from tasks.base_tasks import xml2json, dataverse_mapper, \
    dataverse_import, update_publication_date, doi_minter
from utils import get_field_from_dataverse_json

CBS_MAPPING_FILE_PATH = os.getenv('CBS_MAPPING_FILE_PATH')
CBS_TEMPLATE_FILE_PATH = os.getenv('CBS_TEMPLATE_FILE_PATH')
CBS_DATAVERSE_ALIAS = os.getenv('CBS_DATAVERSE_ALIAS')


@flow
def cbs_metadata_ingestion(file_path):
    json_metadata = xml2json(file_path)
    if not json_metadata:
        return Failed(message='Unable to transform from xml to json.')

    mapped_metadata = dataverse_mapper(json_metadata, CBS_MAPPING_FILE_PATH,
                                       CBS_TEMPLATE_FILE_PATH, False)
    if not mapped_metadata:
        return Failed(message='Unable to map metadata.')
    doi = doi_minter(mapped_metadata)
    if not doi:
        return Failed(message='Failed to mint or update DOI with Datacite API')

    import_response = dataverse_import(mapped_metadata, CBS_DATAVERSE_ALIAS,
                                       doi)
    if not import_response:
        return Failed(message='Unable to import dataset into Dataverse.')

    publication_date = get_field_from_dataverse_json(mapped_metadata,
                                                     'citation',
                                                     'distributionDate')
    if publication_date["value"]:
        return Failed(message='No publication date in metadata')

    pub_date_response = update_publication_date(publication_date["value"],
                                                doi)
    if not pub_date_response:
        return Failed(message='Unable to update publication date.')

    return Completed(message=file_path + 'ingested successfully.')
