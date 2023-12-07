import json
from datetime import timedelta
from pyDataverse.api import NativeApi
from configuration.config import settings
from prefect import task, get_run_logger
import requests

import utils


@task(timeout_seconds=300, retries=1, cache_expiration=timedelta(minutes=10))
async def xml2json(xml_metadata):
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


@task(timeout_seconds=300, retries=1, cache_expiration=timedelta(minutes=10))
async def dataverse_mapper(json_metadata, mapping_file_path,
                           template_file_path,
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
    result = await utils.async_http_request_handler(url, headers, data)
    return result


@task(timeout_seconds=300, retries=1, cache_expiration=timedelta(minutes=10))
async def dataverse_import(mapped_metadata, settings_dict, doi=None):
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
    result = await utils.async_http_request_handler(url, headers, data)
    return result


@task(timeout_seconds=300, retries=1, cache_expiration=timedelta(minutes=10))
async def update_publication_date(publication_date, pid, settings_dict):
    """ Sends a request to the publication date updater to update the pub date.

    The dataverse_information field in the data takes two fields:
    base_url: The Dataverse instance URL.
    api_token: The token specific to this DV instance to allow use of the API.

    :param publication_date: The original date of publication.
    :param pid: The DOI of the dataset in question.
    :param settings_dict: dict, contains settings for the current task.
    :return: Response body on success | None on failure.
    """
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
    result = await utils.async_http_request_handler(url, headers, data)
    return result


@task(timeout_seconds=300, retries=1, cache_expiration=timedelta(minutes=10))
async def dataverse_metadata_fetcher(metadata_format, doi, settings_dict):
    """
    Fetches the metadata of a dataset with the given DOI.

    The dataverse_information field in the data takes one field:
    base_url: The source Dataverse from where the metadata is harvested.

    :param metadata_format: string, metadata format e.g. 'dataverse_json'.
    :param doi: string, The DOI of the dataset that gets fetched.
    :param settings_dict: dict, contains settings for the current task
    :return: JSON or None
    """

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    data = {
        'doi': doi,
        'metadata_format': metadata_format,
        "base_url": settings_dict.SOURCE_DATAVERSE_URL,
    }

    url = f"{settings.METADATA_FETCHER_URL}/dataverse-metadata-fetcher"
    result = await utils.async_http_request_handler(url, headers, data)
    return result


@task(timeout_seconds=300, retries=1, cache_expiration=timedelta(minutes=10))
def get_doi_from_dv_json(dataverse_json):
    """ Retrieves the DOI of a dataset from mapped Dataverse JSON

    For mapped metadata the DOI will be mapped to the "datasetPersistentId"
    field in the metadata.

    :param dataverse_json: JSON metadata formatted for the Native API.
    :return: The DOI of the dataset.
    """
    try:
        doi = dataverse_json["persistentUrl"]
    except KeyError:
        return None
    return doi


@task(timeout_seconds=300, retries=1, cache_expiration=timedelta(minutes=10))
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


@task(timeout_seconds=300, retries=1, cache_expiration=timedelta(minutes=10))
async def doi_minter(metadata):
    """
    Mints a DOI for the given dataset using the Datacite API.

    :param metadata: Metadata of the dataset that needs minting.
    :return: Minted DOI
    """
    url = settings.DOI_MINTER_URL

    headers = {
        'Content-Type': 'application/json',
        'Authorization': settings.MINTER_API_TOKEN,
    }

    result = await utils.async_http_request_handler(url, headers, metadata)
    if not result:
        return None
    return result.text.replace('"', '').replace('{', '').replace('}', '')


@task(timeout_seconds=300, retries=1, cache_expiration=timedelta(minutes=10))
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


@task(timeout_seconds=300, retries=1, cache_expiration=timedelta(minutes=10))
async def sanitize_emails(xml_metadata, replacement_email: str = None):
    """ sends data to a services that sanitizes the emails out of the data.

    Emails get replaced by empty string if no replacement email is specified.
    :param xml_metadata: The data to sanitize.
    :param replacement_email: The email to replace any found emails with.
    """
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
    url = settings.EMAIL_SANITIZER_URL
    result = await utils.async_http_request_handler(url, headers, data)
    if not result:
        return None
    return result['data'].encode('utf-8')


@task(timeout_seconds=300, retries=1, cache_expiration=timedelta(minutes=10))
async def refine_metadata(metadata: dict, settings_dict):
    """ Sends the metadata to a service for refinement.

    This type of refinement that is done depends on the endpoint being called.
    This service does not enrich or add metadata, it only cleans-up or refines
    existing metadata.

    :param metadata: The metadata to refine.
    :param settings_dict: The settings dict containing the endpoint to be used.
    """

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    data = {
        'metadata': metadata,
    }

    url = settings.METADATA_REFINER_URL + settings_dict.REFINER_ENDPOINT
    result = await utils.async_http_request_handler(url, headers, data)
    return result


@task
def extract_doi_from_dataverse(settings_dict, alias):
    """
    Method to extract a list of DOI's from a given dataverse
    """
    api = NativeApi(
        base_url=settings_dict.DESTINATION_DATAVERSE_URL,
        api_token=settings_dict.DESTINATION_DATAVERSE_API_KEY
    )
    datasets = api.get_children(parent=alias, children_types=['datasets'])
    pids = []
    for child in datasets:
        pids.append(child['pid'])
    return pids


@task(timeout_seconds=300, retries=1, cache_expiration=timedelta(minutes=10))
async def semantic_enrichment(settings_dict, pid: str):
    """ An API call to a service that enriches the search index.

    The semantic enrichment API takes the keywords of a dataset in Dataverse.
    It then matches those keywords on ELSST terms and adds them to the search
    index of SOLR. This makes them searchable in Dataverse.

    :param settings_dict: Contains settings for the current task.
    :param pid: The pid of the dataset.
    """
    logger = get_run_logger()

    url = settings.SEMANTIC_API_URL
    params = {
        'token': settings_dict.DESTINATION_DATAVERSE_API_KEY,
        'pid': pid,
        'base': settings_dict.DESTINATION_DATAVERSE_URL,
        'skosmosendpoint': settings.ELSST_SKOSMOS_URL,
        'fields': 'prefLabel',
        'vocab': 'elsst-3'
    }

    response = requests.get(url, params=params)

    if not response.ok:
        logger.info(response.text)
        return None
    return response.json()


@task(task_run_name="{endpoint}-enrichment-task", timeout_seconds=300,
      retries=1, cache_expiration=timedelta(minutes=10))
async def enrich_metadata(metadata: dict, endpoint: str) -> dict:
    """ Uses the metadata-enhancer service to enrich the metadata.

    :param metadata: The metadata to enrich.
    :param endpoint: The endpoint that expresses the type of enrichment needed.
    """

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    data = {
        "metadata": metadata,
    }

    url = f"{settings.METADATA_ENHANCER_URL}/{endpoint}"
    result = await utils.async_http_request_handler(url, headers, data)
    return result
