import requests
from prefect import task, get_run_logger

from configuration.config import settings


@task
def get_service_version(service_url, service_name, endpoint):
    """Record the contacted service's version and processing endpoints."""
    return {
        'name': service_name,
        'version': get_deployed_service_version(service_url),
        'endpoint': endpoint,
    }


def get_deployed_service_version(service_url):
    logger = get_run_logger()
    response = None
    try:
        response = requests.get(service_url, timeout=30)
        response.raise_for_status()
        data = response.json()
        version = data.get('version') or data.get('info', {}).get('version')
        if not isinstance(version, str) or not version.strip():
            raise ValueError(f'Missing service version at {service_url}')
        return version
    except (requests.RequestException, ValueError):
        logger.exception('Failed to read service version from %s; response: %s',
                         service_url,
                         response.text[:1000] if response is not None else 'none')
        raise


def store_workflow_version(version_dict):
    """Store a workflow record and return its public retrieval URL."""
    logger = get_run_logger()
    store_url = settings.VERSION_TRACKER_STORE_URL
    response = None
    try:
        retrieve_url = settings.VERSION_TRACKER_PUBLIC_RETRIEVE_URL.rstrip('/')
        if not retrieve_url:
            raise ValueError('VERSION_TRACKER_PUBLIC_RETRIEVE_URL is required')
        response = requests.post(store_url, json=version_dict, timeout=30)
        response.raise_for_status()
        version_id = response.json().get('id')
        if not isinstance(version_id, str) or not version_id.strip():
            raise ValueError('Version tracker returned no document ID')
        return retrieve_url + '/' + version_id
    except (requests.RequestException, ValueError):
        logger.exception('Failed to store workflow version at %s; response: %s',
                         store_url,
                         response.text[:1000] if response is not None else 'none')
        raise
