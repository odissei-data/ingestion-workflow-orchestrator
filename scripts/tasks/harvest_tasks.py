import json

import requests
from prefect import task

from configuration.config import settings


@task(timeout_seconds=300, retries=1)
def oai_harvest_metadata(metadata_prefix, oai_endpoint, bucket_name, verb,
                         harvester_endpoint, timestamp=None, oai_set=None):
    """ A task that harvests metadata using the oai-harvester service.

    This tasks harvests a list of records or identifiers and places the
    harvested data in a specified bucket.

    :param metadata_prefix: The metadata format of the harvested data.
    :param oai_endpoint: The endpoint where the data will be harvested.
    :param bucket_name: The bucket the harvested data will be stored in.
    :param verb: The type of harvest. (ListRecords or ListIdentifiers).
    :param harvester_endpoint: The API of the harvester service.
    :param timestamp: Timestamp from which to start harvesting.
    :param oai_set: A specific set of data that will be harvested.
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
        "verb": verb
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
def harvest_metadata(bucket_name, endpoint):
    """ A task that harvests the LISS dataset metadata.

    The LISS server where we harvest metadata has a different
    implementation than oai-pmh. This task calls the endpoint in the harvester
    service that implements the harvesting protocol that is unique to LISS.

    :param endpoint: The harvester endpoint to call.
    :param bucket_name: The bucket the LISS metadata will be stored in.
    """
    headers = {
        'Content-Type': 'application/json',
        'accept': 'application/json',
        'X-API-Key': settings.HARVESTER_API_TOKEN
    }

    data = {
        "bucket_name": bucket_name,
    }

    url = f"{settings.HARVESTER_URL}/{endpoint}"
    response = requests.post(
        url, headers=headers, data=json.dumps(data)
    )

    if not response.ok:
        raise Exception(
            f'Request failed with status code {response.status_code}: '
            f'{response.text}')

