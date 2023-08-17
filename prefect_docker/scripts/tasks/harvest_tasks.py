import json

import requests
from prefect import task

from configuration.config import settings


@task(timeout_seconds=300, retries=1)
def harvest_metadata(metadata_prefix, oai_endpoint, bucket_name, verb,
                     harvester_endpoint, oai_set=None):
    headers = {
        'Content-Type': 'application/json',
        'accept': 'application/json'
    }

    data = {
        "metadata_prefix": metadata_prefix,
        "oai_endpoint": oai_endpoint,
        "bucket_name": bucket_name,
        "verb": verb
    }

    print(f'data: {data}')

    if oai_set is not None:
        data['oai_set'] = oai_set

    url = f"{settings.HARVESTER_URL}/{harvester_endpoint}"
    print(f'url: {url}')

    response = requests.post(
        url, headers=headers, data=json.dumps(data)
    )

    if not response.ok:
        raise Exception(
            f'Request failed with status code {response.status_code}:'
            f' {response.text}')


@task(timeout_seconds=300, retries=1)
def liss_harvest_metadata(bucket_name):
    headers = {
        'Content-Type': 'application/json',
        'accept': 'application/json'
    }

    data = {
        "bucket_name": bucket_name,
    }

    url = f"{settings.HARVESTER_URL}/start_liss_harvest"

    response = requests.post(
        url, headers=headers, data=json.dumps(data)
    )

    if not response.ok:
        raise Exception(
            f'Request failed with status code {response.status_code}: '
            f'{response.text}')

