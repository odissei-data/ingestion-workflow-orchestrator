import os

from prefect import flow
from prefect.orion.schemas.states import Completed, Failed

from tasks.base_tasks import xml2json, dataverse_mapper, \
    dataverse_import, update_publication_date, get_doi_from_dv_json, \
    add_workflow_versioning_url
from utils import is_lower_level_liss_study

LISS_MAPPING_FILE_PATH = os.getenv('LISS_MAPPING_FILE_PATH')
LISS_TEMPLATE_FILE_PATH = os.getenv('LISS_TEMPLATE_FILE_PATH')
LISS_DATAVERSE_ALIAS = os.getenv('LISS_DATAVERSE_ALIAS')


@flow
def liss_metadata_ingestion(file_path, version):
    json_metadata = xml2json(file_path)
    if not json_metadata:
        return Failed(message='Unable to transform from xml to json')

    mapped_metadata = dataverse_mapper(json_metadata, LISS_MAPPING_FILE_PATH,
                                       LISS_TEMPLATE_FILE_PATH)
    if not mapped_metadata:
        return Failed(message='Unable to map metadata')

    if is_lower_level_liss_study(mapped_metadata)[0]:
        return Completed(message='Lower level LISS study')

    doi = get_doi_from_dv_json(mapped_metadata)
    if not doi:
        return Failed(message='Missing DOI in mapped metadata.')

    mapped_metadata = add_workflow_versioning_url(mapped_metadata, version)

    import_response = dataverse_import(mapped_metadata, LISS_DATAVERSE_ALIAS,
                                       doi)
    if not import_response:
        return Failed(message='Unable to import dataset into Dataverse')

    fields = mapped_metadata['datasetVersion']['metadataBlocks']['citation'][
        'fields']
    publication_date = next((field for field in fields if
                             field.get('typeName') == 'distributionDate'),
                            None)
    if publication_date["value"]:
        pub_date_response = update_publication_date(publication_date["value"],
                                                    doi)
        if not pub_date_response:
            return Failed(message='Unable to update publication date')

    return Completed(message=file_path + " ingested successfully")
