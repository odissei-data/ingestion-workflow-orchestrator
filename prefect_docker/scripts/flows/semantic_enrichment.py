import requests
from configuration.config import settings
from prefect import flow, task
from prefect.orion.schemas.states import Failed

from tasks.base_tasks import semantic_enrichment


@flow
def dataverse_semantic_enrichment(dataverse_url, subverse, api_token,
                                  settings_dict_name):
    """
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
    api_endpoint = f"{dataverse_url}/api/dataverses/{subverse}/contents"
    headers = {"X-Dataverse-key": api_token,
               'Content-Type': 'application/json'}

    response = requests.get(api_endpoint, headers=headers)
    if response.status_code == 200:
        datasets = response.json()
        doi_list = [reformat_doi(dataset['persistentUrl'])
                    for dataset in datasets["data"]]
        return doi_list
    else:
        print(f"Request failed with status code: {response.status_code}")
        return None


def reformat_doi(unstructured_doi):
    doi = 'doi:' + unstructured_doi.split("/", 3)[3]
    return doi
