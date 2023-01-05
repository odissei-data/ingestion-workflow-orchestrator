import os

from prefect import flow
from prefect.orion.schemas.states import Completed, Failed
from tasks.base_tasks import xml2json, dataverse_mapper, \
    dataverse_import, update_publication_date, add_workflow_versioning_url

CBS_MAPPING_FILE_PATH = os.getenv('CBS_MAPPING_FILE_PATH')
CBS_TEMPLATE_FILE_PATH = os.getenv('CBS_TEMPLATE_FILE_PATH')
CBS_DATAVERSE_ALIAS = os.getenv('CBS_DATAVERSE_ALIAS')


@flow
def cbs_metadata_ingestion(file_path, version):
    json_metadata = xml2json(file_path)
    if not json_metadata:
        return Failed(message='Unable to transform from xml to json.')

    mapped_metadata = dataverse_mapper(json_metadata, CBS_MAPPING_FILE_PATH,
                                       CBS_TEMPLATE_FILE_PATH, False)
    if not mapped_metadata:
        return Failed(message='Unable to map metadata.')

    mapped_metadata = add_workflow_versioning_url(mapped_metadata, version)

    import_response = dataverse_import(mapped_metadata, CBS_DATAVERSE_ALIAS)
    if not import_response:
        return Failed(message='Unable to import dataset into Dataverse.')

    doi = import_response.json()['data']['persistentId']
    fields = mapped_metadata['datasetVersion']['metadataBlocks']['citation'][
        'fields']
    publication_date = next((field for field in fields if
                             field.get('typeName') == 'distributionDate'),
                            {})
    if publication_date["value"]:
        pub_date_response = update_publication_date(publication_date["value"],
                                                    doi)
        if not pub_date_response:
            return Failed(message='Unable to update publication date.')
    return Completed(message=file_path + 'ingested successfully.')
