"""Check that every service the worker calls is ready.

Run by hand or at the end of a deploy: `python readiness.py` prints one line
per check and exits 1 when any fails. Every entry flow runs `check_readiness`
first; on failure it pauses all deployments and fails the run.
"""
import sys
from urllib.parse import urljoin

import requests
from prefect import get_client, get_run_logger, task

from configuration.config import settings

# Setting holding the service URL, and the path to check on it. The paths are
# relative, so a service behind a path prefix keeps it: the version tracker's
# .../version-tracker/store becomes .../version-tracker/ready.
CHECKS = [
    ('HARVESTER_URL', 'ready'),
    ('VERSION_TRACKER_STORE_URL', 'ready'),
    ('DATAVERSE_MAPPER_URL', 'health'),
    ('METADATA_REFINER_URL', 'health'),
    ('METADATA_ENHANCER_URL', 'health'),
    ('DANS_TRANSFORMER_SERVICE', 'openapi.json'),
    ('S3_ENDPOINT_URL', 'healthz'),
    ('ODISSEI_URL', 'api/info/version'),
]


def check(url, headers=None):
    """Return 'ok', or the HTTP status or error name of a failed request."""
    try:
        response = requests.get(url, headers=headers, timeout=5)
    except requests.RequestException as error:
        return type(error).__name__
    return 'ok' if response.ok else f'HTTP {response.status_code}'


def run_checks():
    """Return (url, result) for every check."""
    urls = [urljoin(settings[name], path) for name, path in CHECKS]
    results = [(url, check(url)) for url in urls]
    # The worker's API token must be valid on the destination Dataverse.
    me = urljoin(settings.ODISSEI_URL, 'api/users/:me')
    results.append((me, check(me, {'X-Dataverse-key': settings.ODISSEI_API_KEY})))
    return results


@task
def check_readiness():
    results = run_checks()
    lines = '\n'.join(f'{url} {result}' for url, result in results)
    if all(result == 'ok' for _, result in results):
        get_run_logger().info('All services ready:\n%s', lines)
        return
    # Reads one page of deployments (the server default is 200).
    with get_client(sync_client=True) as client:
        for deployment in client.read_deployments():
            client.pause_deployment(deployment.id)
    raise RuntimeError(f'Services not ready; all deployments paused:\n{lines}')


if __name__ == '__main__':
    results = run_checks()
    for url, result in results:
        print(url, result)
    sys.exit(0 if all(result == 'ok' for _, result in results) else 1)
