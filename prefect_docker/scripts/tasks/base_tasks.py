import json

from configuration.config import settings
from prefect import task, get_run_logger
import requests
from requests.structures import CaseInsensitiveDict

import utils


@task
def xml2json(xml_metadata):
    """ Sends XML to the transformer server, receives JSON with same hierarchy.

    Sends a request to the transformer endpoint for transformation
    from xml to json. Needs an authorization token to use the transformer API.

    :param xml_metadata: The XML contents
    :return: Plain JSON metadata | None on failure.
    """
    logger = get_run_logger()
    headers = {
        'Content-Type': 'application/xml',
        'Authorization': settings.XML2JSON_API_TOKEN,
    }

    url = f"{settings.DANS_TRANSFORMER_SERVICE}/transform-xml-to-json/true"
    response = requests.post(
        url,
        headers=headers, data=xml_metadata
    )

    if not response.ok:
        logger.info(response.text)
        return None

    return response.json()


@task
def dataverse_mapper(json_metadata, mapping_file_path, template_file_path,
                     has_doi=True):
    """ Sends plain JSON to the mapper service, receives JSON formatted for DV.

    Uses the template and mapping file in the resources volume, and metadata
    represented as JSON to send a request  to the mapper service.

    :param mapping_file_path: The path to where the mapping lives.
    :param template_file_path: The path to where the template lives.
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
    with open(template_file_path) as f:
        template = json.load(f)
        data['template'] = template
    with open(mapping_file_path) as f:
        mapping = json.load(f)
        data['mapping'] = mapping
    data["has_existing_doi"] = has_doi

    url = f"{settings.DATAVERSE_MAPPER_URL}/mapper"
    response = requests.post(
        url,
        headers=headers, data=json.dumps(data)
    )
    if not response.ok:
        logger.info(response.text)
        return None
    return response.json()


@task
def dataverse_import(mapped_metadata, settings_dict, doi=None):
    """ Sends a request to the import service to import the given metadata.

    The dataverse_information field in the data takes three fields:
    base_url: The Dataverse instance URL.
    dt_alias: The Dataverse or sub-Dataverse you want to target for the import.
    api_token: The token specific to this DV instance to allow use of the API.

    :param mapped_metadata: JSON metadata formatted for the Native API.
    :param settings_dict: dict, contains settings for the current task
    :param doi: The DOI of the dataset that is being imported.
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
            "base_url": settings_dict.DESTINATION_DATAVERSE_URL,
            "dt_alias": settings_dict.ALIAS,
            "api_token": settings_dict.DESTINATION_DATAVERSE_API_KEY
        }}

    if doi:
        data['doi'] = doi

    url = f"{settings.DATAVERSE_IMPORTER_URL}/importer"
    response = requests.post(
        url,
        headers=headers,
        data=json.dumps(data)
    )
    if not response.ok:
        logger.info(response.text)
        return None
    return response


@task
def update_publication_date(publication_date, pid, settings_dict):
    """ Sends a request to the publication date updater to update the pub date.

    The dataverse_information field in the data takes two fields:
    base_url: The Dataverse instance URL.
    api_token: The token specific to this DV instance to allow use of the API.

    :param publication_date: The original date of publication.
    :param pid: The DOI of the dataset in question.
    :param settings_dict: dict, contains settings for the current task
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
            "base_url": settings_dict.DESTINATION_DATAVERSE_URL,
            "api_token": settings_dict.DESTINATION_DATAVERSE_API_KEY
        }
    }

    url = f"{settings.PUBLICATION_DATA_UPDATER_URL}/publication-date-updater"
    response = requests.post(
        url,
        headers=headers,
        data=json.dumps(data)
    )
    if not response.ok:
        logger.info(response.text)
        return None
    return response


@task
def dataverse_metadata_fetcher(metadata_format, doi, settings_dict):
    """
    Fetches the metadata of a dataset with the given DOI.

    The dataverse_information field in the data takes two fields:
    base_url: The source Dataverse from where the metadata is harvested.
    api_token: The token specific to this DV instance to allow use of the API.

    :param metadata_format: string, metadata format e.g. 'dataverse_json'.
    :param doi: string, The DOI of the dataset that gets fetched.
    :param settings_dict: dict, contains settings for the current task
    :return: JSON or None
    """
    logger = get_run_logger()
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    data = {
        'doi': doi,
        'metadata_format': metadata_format,
        "dataverse_information": {
            "base_url": settings_dict.SOURCE_DATAVERSE_URL,
            "api_key": "hello"
        }
    }

    url = f"{settings.METADATA_FETCHER_URL}/dataverse-metadata-fetcher"
    response = requests.post(
        url,
        headers=headers,
        data=json.dumps(data)
    )

    if not response.ok:
        logger.info(response.text)
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
def format_license(ds_license):
    if ds_license == 'CC0':
        ds_license = 'CC0 1.0'
    elif 'uri' in ds_license:
        ds_license = utils.retrieve_license_name(ds_license['uri'])
    return ds_license


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
    if dataset_contact:
        for dataset_contact in dataset_contact["value"]:
            dataset_contact["datasetContactEmail"] = {
                "typeName": "datasetContactEmail",
                "multiple": False,
                "typeClass": "primitive",
                "value": "portal@odissei.nl"
            }
    else:
        fields.append({
            "typeName": "datasetContact",
            "multiple": True,
            "typeClass": "compound",
            "value": [
                {
                    "datasetContactEmail": {
                        "typeName": "datasetContactEmail",
                        "multiple": False,
                        "typeClass": "primitive",
                        "value": "portal@odissei.nl"
                    }
                }
            ]
        })
        return dataverse_json
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


@task
def add_workflow_versioning_url(mapped_metadata, version):
    """ Adds the workflow versioning URL to the metadata.

    The workflow version URL that was created is added to the provenance
    metadata block.

    :param mapped_metadata: The Dataverse formatted metadata.
    :param version: The version URL.
    :return: The metadata containing the version URL in the provenance block.
    """
    keys = ['datasetVersion', 'metadataBlocks', 'provenance']
    d = mapped_metadata

    for key in keys:
        if key not in d:
            d[key] = {}
        d = d[key]

    d['fields'] = [
        {
            "typeName": "workflow",
            "multiple": False,
            "typeClass": "compound",
            "value": {
                "workflowURI": {
                    "typeName": "workflowURI",
                    "multiple": False,
                    "typeClass": "primitive",
                    "value": version
                },
            }
        }
    ]
    return mapped_metadata


@task
def sanitize_emails(xml_metadata, replacement_email: str = None):
    logger = get_run_logger()
    if replacement_email is None:
        replacement_email = ""

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    data = {
        'data': xml_metadata.decode('utf-8'),
        'replacement_email': replacement_email
    }
    response = requests.post(
        settings.EMAIL_SANITIZER_URL, headers=headers,
        data=json.dumps(data))

    if not response.ok:
        logger.info(response.text)
        return None
    data = response.json()
    return data['data'].encode('utf-8')
