import os

from config import settings
from prefect import flow
from prefect.orion.schemas.states import Completed, Failed

from tasks.base_tasks import xml2json, dataverse_mapper, \
    dataverse_import, update_publication_date, get_license, \
    get_doi_from_dv_json, add_workflow_versioning_url


@flow
def easy_metadata_ingestion(file_path, alias, version):
    json_metadata = xml2json(file_path)
    if not json_metadata:
        return Failed(message='Unable to transform from xml to json')

    mapped_metadata = dataverse_mapper(
        json_metadata,
        settings.EASY_MAPPING_FILE_PATH,
        settings.EASY_TEMPLATE_FILE_PATH
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

    import_response = dataverse_import(mapped_metadata, alias,
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
