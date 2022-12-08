import json
import os
import requests
from prefect import task, get_run_logger
from requests.structures import CaseInsensitiveDict

import utils

DATAVERSE_URL = os.getenv('DATAVERSE_URL')
DATAVERSE_ALIAS = os.getenv('DATAVERSE_ALIAS')
SOURCE_DATAVERSE_URL = os.getenv('SOURCE_DATAVERSE_URL')

DATAVERSE_API_TOKEN = os.getenv('DATAVERSE_API_TOKEN')
XML2JSON_API_TOKEN = os.getenv('XML2JSON_API_TOKEN')

MAPPING_FILE_PATH = os.getenv('MAPPING_FILE_PATH')
TEMPLATE_FILE_PATH = os.getenv('TEMPLATE_FILE_PATH')


@task
def xml2json(file_path):
    """ Sends XML to the transformer server, receives JSON with same hierarchy.

    Sends a request to the transformer endpoint for transformation
    from xml to json. Needs an authorization token to use the transformer API.

    :param file_path: The filepath of the xml file.
    :return: Plain JSON metadata | None on failure.
    """
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
def dataverse_mapper(json_metadata, has_doi=True):
    """ Sends plain JSON to the mapper service, receives JSON formatted for DV.

    Uses the template and mapping file in the resources volume, and metadata
    represented as JSON to send a request  to the mapper service.

    :param has_doi: Boolean that tells if the metadata contains a doi.
    :param json_metadata: Plain JSON metadata.
    :return: JSON metadata formatted for the Native API | None on failure.
    """
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
    data["has_existing_doi"] = has_doi

    response = requests.post('http://host.docker.internal:8080/mapper',
                             headers=headers, data=json.dumps(data))
    if not response.ok:
        logger.info(response.json())
        return None
    return response.json()


@task
def dataverse_import(mapped_metadata, doi=None):
    """ Sends a request to the import service to import the given metadata.

    The dataverse_information field in the data takes three fields:
    base_url: The Dataverse instance URL.
    dt_alias: The Dataverse or sub-dataverse you want to target for the import.
    api_token: The token specific to this DV instance to allow use of the API.

    :param doi: The DOI of the dataset that is being imported.
    :param mapped_metadata: JSON metadata formatted for the Native API.
    :return: Response body on success | None on failure.
    """
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

    if doi:
        data['doi'] = doi

    response = requests.post('http://host.docker.internal:8090/importer',
                             headers=headers, data=json.dumps(data))
    if not response.ok:
        logger.info(response.json())
        return None
    return response


@task
def update_publication_date(publication_date, pid):
    """ Sends a request to the publication date updater to update the pub date.

    The dataverse_information field in the data takes two fields:
    base_url: The Dataverse instance URL.
    api_token: The token specific to this DV instance to allow use of the API.

    :param publication_date: The original date of publication.
    :param pid: The DOI of the dataset in question.
    :return: Response body on success | None on failure.
    """
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
def dataverse_metadata_fetcher(doi, metadata_format):
    """ Fetches the metadata of a dataset with the given DOI.

     The dataverse_information field in the data takes two fields:
    base_url: The Dataverse instance URL.
    api_token: The token specific to this DV instance to allow use of the API.

    :param doi: The DOI of the dataset that gets fetched.
    :param metadata_format: The format of the metadata. e.g. 'dataverse_json'.
    :return:
    """
    logger = get_run_logger()
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    data = {
        'pid': doi,
        'metadata_format': metadata_format,
        "dataverse_information": {
            "base_url": SOURCE_DATAVERSE_URL,
            "api_token": DATAVERSE_API_TOKEN
        }
    }

    response = requests.post(
        'http://host.docker.internal:8888/dataverse-metadata-fetcher',
        headers=headers, data=json.dumps(data))
    if not response.ok:
        logger.info(response.json())
        return None
    return response.json()


@task
def get_doi_from_dv_json(dataverse_json):
    """ Retrieves the DOI of a dataset from mapped Dataverse JSON

    For mapped metadata the DOI will be mapped to the "datasetPersistentId"
    field in the metadata.

    :param dataverse_json: JSON metadata formatted for the Native API.
    :return: The DOI of the dataset.
    """
    try:
        doi = dataverse_json["datasetVersion"]["datasetPersistentId"]
    except KeyError:
        return None
    return doi


@task
def get_doi_from_header(json_metadata):
    """ Retrieves the DOI from the header in the basic JSON metadata.

    For data exported from a Dataverse instance, the DOI will be in the header
    of the metadata. get_doi_from_header retrieves the DOI from metadata
    that has already been transformed from XML to basic JSON.

    :param json_metadata: Plain JSON metadata of a dataset.
    :return: The DOI of the dataset.
    """
    try:
        doi = json_metadata["result"]["record"]["header"]["identifier"]
    except KeyError:
        return None
    return doi


@task
def get_license(json_metadata):
    """ Retrieves the license name from the given metadata.

    Tries to access the key that contains the license of the dataset.
    If successful it fetches the license name, else it uses a basic license.

    :param json_metadata: Plain JSON metadata of a dataset.
    :return: license name of the dataset.
    """
    try:
        metadata_license = json_metadata["result"]["record"]["metadata"][
            "ddi:codeBook"]["ddi:stdyDscr"]["ddi:dataAccs"]["ddi:useStmt"][
            "ddi:conditions"]
        if not isinstance(metadata_license, str):
            metadata_license = metadata_license['#text']
        lic = utils.retrieve_license_name(metadata_license)
        return lic

    except KeyError:
        return 'DANS Licence'


@task
def add_contact_email(dataverse_json):
    """ Adds a contact email to dataverse JSON.

    If metadata exported from a Dataverse is missing the contact email,
    add_contact_email can be used to add a contact email.
    TODO: make the email value an env variable.

    :param dataverse_json: Dataverse JSON that is missing the contact email.
    :return: dataverse JSON with the contact email added.
    """
    fields = dataverse_json['datasetVersion']['metadataBlocks']['citation'][
        'fields']
    dataset_contact = next((field for field in fields if
                            field.get('typeName') == 'datasetContact'), None)
    if dataset_contact["value"]:
        dataset_contact["value"][0]["datasetContactEmail"] = {
            "typeName": "datasetContactEmail",
            "multiple": False,
            "typeClass": "primitive",
            "value": "portal@odissei.com"
        }
    return dataverse_json


@task
def doi_minter(metadata):
    """
    TODO

    :param metadata:
    :return:
    """
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
