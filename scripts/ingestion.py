import json
import os
import requests
from prefect import flow, task
from prefect.orion.schemas.states import Completed, Failed

DATAVERSE_URL = os.getenv('DATAVERSE_URL')
DATAVERSE_ALIAS = os.getenv('DATAVERSE_ALIAS')

DATAVERSE_API_TOKEN = os.getenv('DATAVERSE_API_TOKEN')
XML2JSON_API_TOKEN = os.getenv('XML2JSON_API_TOKEN')

MAPPING_FILE_PATH = os.getenv('MAPPING_FILE_PATH')
TEMPLATE_FILE_PATH = os.getenv('TEMPLATE_FILE_PATH')


@flow
def ingestion_pipeline():
    for filename in os.listdir('/cbs-metadata'):
        file_path = os.path.join('/cbs-metadata', filename)
        if os.path.isfile(file_path) and 'dsc' in file_path:
            cbs_metadata_ingestion(file_path, return_state=True)


@flow
def cbs_metadata_ingestion(file_path):
    json_metadata = xml2json(file_path)
    if not json_metadata:
        return Failed(message='Unable to transform from xml to json')

    mapped_metadata = dataverse_mapper(json_metadata)
    if not mapped_metadata:
        return Failed(message='Unable to map metadata')

    import_response = dataverse_import(mapped_metadata)
    if not import_response:
        return Failed(message='Unable to import dataset into Dataverse')

    pid = import_response.json()['data']['persistentId']
    fields = mapped_metadata['datasetVersion']['metadataBlocks']['citation'][
        'fields']
    publication_date = next((field for field in fields if
                             field.get('typeName') == 'distributionDate'),
                            None)
    if publication_date:
        response = update_publication_date(publication_date["value"], pid)
        if not response.ok:
            return Failed(message='Unable to update publication date')
    else:
        return Completed(message=file_path + " ingested successfully")


@task()
def xml2json(file_path):
    headers = {
        'Content-Type': 'application/xml',
        'Authorization': XML2JSON_API_TOKEN,
    }
    with open(file_path, 'rb') as data:
        response = requests.post(
            'https://transformer.labs.dans.knaw.nl/'
            'transform-xml-to-json/true',
            headers=headers, data=data.read())
        if not response.ok:
            return None
    return response.json()


@task
def dataverse_mapper(json_metadata):
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    data = {'metadata': json_metadata}
    with open(TEMPLATE_FILE_PATH) as f:
        template = json.load(f)
        data['template'] = template
    with open(MAPPING_FILE_PATH) as f:
        mapping = json.load(f)
        data['mapping'] = mapping

    response = requests.post('http://host.docker.internal:8080/mapper',
                             headers=headers, data=json.dumps(data))
    if not response.ok:
        return None
    return response.json()


@task
def dataverse_import(mapped_metadata):
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    data = {
        "metadata": mapped_metadata,
        "dataverse_information": {
            "base_url": DATAVERSE_URL,
            "dt_alias": DATAVERSE_ALIAS,
            "api_token": DATAVERSE_API_TOKEN
        }}

    response = requests.post('http://host.docker.internal:8090/importer',
                             headers=headers, data=json.dumps(data))
    if not response.ok:
        return None
    return response


@task
def update_publication_date(publication_date, pid):
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    data = {
        'pid': pid,
        'publication_date': publication_date,
        "dataverse_information": {
            "base_url": DATAVERSE_URL,
            "api_token": DATAVERSE_API_TOKEN
        }
    }

    response = requests.post(
        'http://host.docker.internal:8081/publication-date-updater',
        headers=headers, data=json.dumps(data))
    if not response.ok:
        return None
    return response


cbs_metadata_ingestion(
    "/resources/test-data/oai_easy_dans_knaw_nl_easy_dataset_204565.xml")
