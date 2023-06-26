import requests
from configuration.config import settings
from prefect import flow, task
from prefect.orion.schemas.states import Failed

from tasks.base_tasks import semantic_enrichment


@flow
def dataverse_semantic_enrichment(dataverse_url, subverse, api_token,
                                  settings_dict_name):
    """ Calls the semantic enrichment API for a set of datasets.

    Enriches the solr index of a dataverse instance with ELSST terms matched
    on the keywords in the metadata of a dataset. The list of pids point to the
    datasets that need to be enriched.

    :param dataverse_url: example: portal.staging.odissei.nl
    :param subverse: example: cbs
    :param api_token: the API token of the dataverse instance.
    :param settings_dict_name: The name of the dict that needs to be used,
     can be found in odissei_settings. always in capital letters. example: DANS
    """
    settings_dict = getattr(settings, settings_dict_name)
    pids = extract_dataverse_pids(dataverse_url, subverse, api_token)
    if not pids:
        return Failed(message="Unable to extract pids from dataverse")
    for pid in pids:
        enrichment_response = semantic_enrichment(settings_dict, pid)
        if not enrichment_response:
            return Failed(message="Unable to add enrichments.")


@task
def extract_dataverse_pids(dataverse_url, subverse, api_token):
    """ Extracts the Persistent Identifiers (PIDs) of datasets from a Dataverse
     subverse.

    :param dataverse_url: The base URL of the Dataverse installation.
    :param subverse: The name of the subverse containing the datasets.
    :param api_token: The API token for authentication.
    :return: A list of DOIs of datasets, or None if the request failed.
    """
    api_endpoint = f"{dataverse_url}/api/dataverses/{subverse}/contents"
    headers = {"X-Dataverse-key": api_token,
               'Content-Type': 'application/json'}

    response = requests.get(api_endpoint, headers=headers)
    if response.status_code == 200:
        datasets = response.json()
        doi_list = [format_doi(dataset['persistentUrl'])
                    for dataset in datasets["data"]]
        return doi_list
    else:
        print(f"Request failed with status code: {response.status_code}")
        return None


def format_doi(unstructured_doi):
    """Formats an unstructured DOI by adding the 'doi:' prefix.

    The original DOI is in an url format:
     https://doi.org/10.57934/0b01e4108001d345
    The DOI should be in the following format:
     doi:10.57934/0b01e4108001d345

    :param unstructured_doi: The unstructured DOI extracted from the dataset.
    :return: doi: The reformatted DOI with the 'doi:' prefix.
    """
    doi = 'doi:' + unstructured_doi.split("/", 3)[3]
    return doi
