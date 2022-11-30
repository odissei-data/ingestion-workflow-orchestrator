import json
import os
import requests
from prefect import task, get_run_logger
from requests.structures import CaseInsensitiveDict

import utils

DATAVERSE_URL = os.getenv('DATAVERSE_URL')
DATAVERSE_ALIAS = os.getenv('DATAVERSE_ALIAS')

DATAVERSE_API_TOKEN = os.getenv('DATAVERSE_API_TOKEN')
XML2JSON_API_TOKEN = os.getenv('XML2JSON_API_TOKEN')

MAPPING_FILE_PATH = os.getenv('MAPPING_FILE_PATH')
TEMPLATE_FILE_PATH = os.getenv('TEMPLATE_FILE_PATH')


@task
def xml2json(file_path):
    logger = get_run_logger()
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
            logger.info(response.json())
            return None
    return response.json()


@task
def dataverse_mapper(json_metadata):
    logger = get_run_logger()
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
    data["has_existing_doi"] = True

    response = requests.post('http://host.docker.internal:8080/mapper',
                             headers=headers, data=json.dumps(data))
    if not response.ok:
        logger.info(response.json())
        return None
    return response.json()


@task
def dataverse_import(mapped_metadata):
    logger = get_run_logger()
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
        logger.info(response.json())
        return None
    return response


@task
def update_publication_date(publication_date, pid):
    logger = get_run_logger()
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
        logger.info(response.json())
        return None
    return response


@task
def get_license(json_metadata):
    try:
        metadata_license = json_metadata["result"]["record"]["metadata"][
            "ddi:codeBook"]["ddi:stdyDscr"]["ddi:dataAccs"]["ddi:useStmt"][
            "ddi:conditions"]
        if not isinstance(metadata_license, str):
            metadata_license = metadata_license['#text']
        lic = utils.retrieve_license(metadata_license)
        return lic

    except KeyError:
        return 'DANS MA KI Licence'


@task
def doi_minter(metadata):
    dataverse_json = json.dumps(metadata)
    url = "http://0.0.0.0:8566/submit-to-datacite"

    headers = CaseInsensitiveDict()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer @km1-10122004-lamA',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    response = requests.post(url, headers=headers, data=dataverse_json)
    doi = response.text.replace('"', '').replace('{', '').replace('}', '')
    return doi
