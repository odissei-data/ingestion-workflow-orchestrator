import json
from datetime import timedelta

from configuration.config import settings
from prefect import task, get_run_logger
import requests

import utils


@task(timeout_seconds=300, retries=1, cache_expiration=timedelta(minutes=10))
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

@task(timeout_seconds=300, retries=1, cache_expiration=timedelta(minutes=10))
def xml2dvjson(xml_metadata):
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

    url = f"{settings.DANS_TRANSFORMER_SERVICE}/transform/{settings.XSLT_TRANSFORMER_NAME}"
    response = requests.post(
        url,
        headers=headers, data=xml_metadata
    )

    if not response.ok:
        logger.info(response.text)
        return None

    return response.json()['result']

@task(timeout_seconds=300, retries=1, cache_expiration=timedelta(minutes=10))
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


@task(timeout_seconds=300, retries=1, cache_expiration=timedelta(minutes=10))
def dataverse_import(mapped_metadata, settings_dict, doi):
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
        "X-Dataverse-key": settings_dict.DESTINATION_DATAVERSE_API_KEY,
        "Content-type": "application/json"
    }

    url = f"{settings_dict.DESTINATION_DATAVERSE_URL}/api/dataverses/" \
        f"{settings_dict.ALIAS}/datasets/:import?pid={doi}&release=no"

    response = requests.post(url, headers=headers, json=mapped_metadata)

    if not response.ok:
        logger.info(response.text)
        return None
    return response


@task(timeout_seconds=300, retries=1, cache_expiration=timedelta(minutes=10))
def update_publication_date(publication_date, pid, settings_dict):
    """ Sends a request to the dataverse target to update the publication date.

    This task updates the publication date of a given pid in the destination
    dataverse. It uses the experimental dataverse API to achieve this.

    :param publication_date: The original date of publication.
    :param pid: The DOI of the dataset in question.
    :param settings_dict: dict, contains settings for the current task.
    :return: Response body on success | None on failure.
    """
    logger = get_run_logger()

    headers = {
        "X-Dataverse-key": settings_dict.DESTINATION_DATAVERSE_API_KEY,
        'Content-Type': 'application/ld+json'}

    url = f'{settings_dict.DESTINATION_DATAVERSE_URL}/api/datasets/' \
        f':persistentId/actions/:releasemigrated?persistentId={pid}'

    publication_date = {
        "schema:datePublished": f'{publication_date}',
        "@context": {"schema": "http://schema.org/"}}

    response = requests.post(url, data=json.dumps(publication_date),
                             headers=headers)

    if not response.ok:
        logger.info(response.text)
        return None
    return response


@task(timeout_seconds=300, retries=1, cache_expiration=timedelta(minutes=10))
def dataverse_metadata_fetcher(metadata_format, doi, settings_dict):
    """
    Fetches the metadata of a dataset with the given DOI.

    The dataverse_information field in the data takes one field:
    base_url: The source Dataverse from where the metadata is harvested.

    :param metadata_format: string, metadata format e.g. 'dataverse_json'.
    :param doi: string, The DOI of the dataset that gets fetched.
    :param settings_dict: dict, contains settings for the current task
    :return: JSON or None
    """
    logger = get_run_logger()

    url = f'{settings_dict.SOURCE_DATAVERSE_URL}/api/datasets/export?' \
        f'exporter={metadata_format}&persistentId={doi}'

    response = requests.get(url)

    if not response.ok:
        logger.info(response.text)
        return None
    return response.json()


@task(name="Dataverse dataset check status", timeout_seconds=300, retries=1,
      cache_expiration=timedelta(minutes=10))
def dataverse_dataset_check_status(doi, dataverse_url):
    """
    Checks the status of a dataset in Dataverse.

    This function sends a GET request to the Dataverse API to check the status
    of a dataset identified by its DOI. The status codes returned by the API
    indicate the following:
    - 200: Dataset exists
    - 404: Dataset does not exist
    - 403: Dataset is deaccessioned

    :param doi: The DOI of the dataset to check.
    :param dataverse_url: The base URL of the Dataverse instance.
    :return: The status code (200, 403, 404) or None on failure.
    """
    logger = get_run_logger()

    url = f"{dataverse_url}/api/datasets/export?exporter=dcterms&" \
        f"persistentId={doi}"
    response = requests.get(url)

    if response.status_code in (200, 403, 404):
        return response.status_code

    logger.info(f'response.text: {response.text}')
    return None


@task(name="Deleting dataset", timeout_seconds=300, retries=1,
      cache_expiration=timedelta(minutes=10))
def delete_dataset(pid, settings_dict):
    """
    Deletes a dataset from Dataverse.

    This function sends a DELETE request to the Dataverse API to delete
     a dataset identified by its persistent identifier (PID).

    :param pid: The persistent identifier of the dataset to delete.
    :param settings_dict: A dictionary containing settings for current task,
                          including the Dataverse API key and URL.
    :return: The response object if the deletion is successful, otherwise None.
    """
    headers = {
        "X-Dataverse-key": settings_dict.DESTINATION_DATAVERSE_API_KEY
    }

    logger = get_run_logger()
    url = f"{settings_dict.DESTINATION_DATAVERSE_URL}/api/datasets/" \
        f":persistentId/destroy/?persistentId={pid}"
    response = requests.delete(url, headers=headers)

    if response and response.status_code == 200:
        return response

    logger.info(f'response.text: {response.text}')
    return None


@task(timeout_seconds=300, retries=1, cache_expiration=timedelta(minutes=10))
def get_doi_from_dv_json(dataverse_json):
    """ Retrieves the DOI of a dataset from mapped Dataverse JSON

    For mapped metadata the DOI will be mapped to the "persistentUrl"
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
def doi_minter(metadata):
    """
    Mints a DOI for the given dataset using the Datacite API.

    :param metadata: Metadata of the dataset that needs minting.
    :return: Minted DOI
    """
    logger = get_run_logger()

    url = settings.DOI_MINTER_URL

    headers = {
        'Content-Type': 'application/json',
        'Authorization': settings.MINTER_API_TOKEN,
    }

    response = requests.post(url, headers=headers, data=json.dumps(metadata))
    if not response.ok:
        logger.info(response.text)
        return None
    doi = response.text.replace('"', '').replace('{', '').replace('}', '')
    return doi


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
def sanitize_emails(xml_metadata, replacement_email: str = None):
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
    response = requests.post(
        settings.EMAIL_SANITIZER_URL, headers=headers,
        data=json.dumps(data))

    if not response.ok:
        logger.info(response.text)
        return None
    data = response.json()
    return data['data'].encode('utf-8')


@task(timeout_seconds=300, retries=1, cache_expiration=timedelta(minutes=10))
def refine_metadata(metadata: dict, settings_dict):
    """ Sends the metadata to a service for refinement.

    This type of refinement that is done depends on the endpoint being called.
    This service does not enrich or add metadata, it only cleans-up or refines
    existing metadata.

    :param metadata: The metadata to refine.
    :param settings_dict: The settings dict containing the endpoint to be used.
    """
    logger = get_run_logger()

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    data = {
        'metadata': metadata,
    }

    response = requests.post(
        settings.METADATA_REFINER_URL + settings_dict.REFINER_ENDPOINT,
        headers=headers, data=json.dumps(data)
    )

    if not response.ok:
        logger.info(response.text)
        return None
    return response.json()


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
def semantic_enrichment(settings_dict, pid: str):
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
def enrich_metadata(metadata: dict, endpoint: str) -> dict:
    """ Uses the metadata-enhancer service to enrich the metadata.

    :param metadata: The metadata to enrich.
    :param endpoint: The endpoint that expresses the type of enrichment needed.
    """
    logger = get_run_logger()

    url = f"{settings.METADATA_ENHANCER_URL}/enrich/{endpoint}"

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    data = {
        "metadata": metadata,
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    if not response.ok:
        logger.info(response.text)
        return {}
    return response.json()
