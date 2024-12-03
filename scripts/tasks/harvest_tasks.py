import json
import requests

from prefect import task, get_run_logger
from configuration.config import settings


@task(timeout_seconds=300, retries=1)
def oai_harvest_metadata(metadata_prefix, oai_endpoint, bucket_name, verb,
                         harvester_endpoint, oai_set=None, timestamp=None):
    """ A task that harvests metadata using the oai-harvester service.

    This tasks harvests a list of records or identifiers and places the
    harvested data in a specified bucket.

    :param metadata_prefix: The metadata format of the harvested data.
    :param oai_endpoint: The endpoint where the data will be harvested.
    :param bucket_name: The bucket the harvested data will be stored in.
    :param verb: The type of harvest. (ListRecords or ListIdentifiers).
    :param harvester_endpoint: The API of the harvester service.
    :param oai_set: A specific set of data that will be harvested.
    :param timestamp: The timestamp from which to start harvesting.
    """
    headers = {
        'Content-Type': 'application/json',
        'accept': 'application/json',
        'X-API-Key': settings.HARVESTER_API_TOKEN
    }

    data = {
        "metadata_prefix": metadata_prefix,
        "oai_endpoint": oai_endpoint,
        "bucket_name": bucket_name,
        "verb": verb,
    }

    if oai_set is not None:
        data['oai_set'] = oai_set

    if timestamp is not None:
        data['timestamp'] = timestamp

    url = f"{settings.HARVESTER_URL}/{harvester_endpoint}"

    response = requests.post(
        url, headers=headers, data=json.dumps(data)
    )

    if not response.ok:
        raise Exception(
            f'Request failed with status code {response.status_code}:'
            f' {response.text}')


@task(timeout_seconds=300, retries=1)
def harvest_metadata(bucket_name, endpoint, timestamp=None):
    """ A task that harvests the LISS dataset metadata.

    The LISS server where we harvest metadata has a different
    implementation than oai-pmh. This task calls the endpoint in the harvester
    service that implements the harvesting protocol that is unique to LISS.

    :param endpoint: The harvester endpoint to call.
    :param bucket_name: The bucket the LISS metadata will be stored in.
    :param timestamp: The timestamp from which to start harvesting (optional).

    """
    headers = {
        'Content-Type': 'application/json',
        'accept': 'application/json',
        'X-API-Key': settings.HARVESTER_API_TOKEN
    }

    data = {
        "bucket_name": bucket_name,
    }

    if timestamp is not None:
        data["timestamp"] = timestamp

    url = f"{settings.HARVESTER_URL}/{endpoint}"
    response = requests.post(
        url, headers=headers, data=json.dumps(data)
    )

    if not response.ok:
        raise Exception(
            f'Request failed with status code {response.status_code}: '
            f'{response.text}')


@task(timeout_seconds=300, retries=1)
def get_most_recent_publication_date(settings_dict):
    logger = get_run_logger()
    api_endpoint = f"{settings_dict.DESTINATION_DATAVERSE_URL}/api/search"
    headers = {"X-Dataverse-key": settings_dict.DESTINATION_DATAVERSE_API_KEY,
               'Content-Type': 'application/json'}

    params = {
        'q': '*',
        'type': 'dataset',
        'subtree': f'{settings_dict.ALIAS}',
        'sort': 'date',
        'per_page': 1
    }

    response = requests.get(api_endpoint, headers=headers, params=params)

    if response.status_code == 200:
        search_results = response.json()
        if search_results['data']['total_count'] > 0:
            most_recent_dataset = search_results['data']['items'][0]
            if 'published_at' in most_recent_dataset:
                most_recent_date = most_recent_dataset['published_at']
                logger.info(
                    f"Most recent publication date: {most_recent_date}")
                return most_recent_date
            else:
                logger.info(
                    "No 'published_at' field found for most recent dataset.")
                return None
        else:
            logger.info("No datasets found in this subverse.")
            return None
    else:
        logger.info(f"Request failed with status code: {response.status_code}")
        return None
