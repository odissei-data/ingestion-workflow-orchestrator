import os
from datetime import datetime
from urllib.parse import urljoin

from prefect import flow
from configuration.config import settings as service_settings
from tasks.versioning_tasks import get_service_version, store_workflow_version

VERSION = os.getenv('VERSION')


@flow
def create_ingestion_workflow_versioning(
        transformer: bool = False,
        mapper: bool = False,
        minter: bool = False,
        refiner: bool = False,
        enhancer: bool = False,
        settings=None,
        transformer_endpoint='transform-xml-to-json/true',
        enhancer_endpoints=('elsst/en',)
):
    """Record the configured services used by this ingestion workflow."""
    version_dict = {
        'workflow_orchestrator': VERSION,
        'created_on': datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
    }

    if transformer:
        base = service_settings.DANS_TRANSFORMER_SERVICE.rstrip('/')
        version_dict['DANS-transformer-service'] = get_service_version(
            base + '/openapi.json', 'DANS-transformer-service',
            base + '/' + transformer_endpoint)

    if mapper:
        base = service_settings.DATAVERSE_MAPPER_URL.rstrip('/')
        version_dict['dataverse-mapper'] = get_service_version(
            base + '/version', 'dataverse-mapper', base + '/mapper')

    if minter:
        endpoint = service_settings.DOI_MINTER_URL
        version_dict['datacite-minter'] = get_service_version(
            urljoin(endpoint, '/openapi.json'), 'datacite-minter', endpoint)

    if refiner:
        base = service_settings.METADATA_REFINER_URL.rstrip('/')
        version_dict['metadata-refiner'] = get_service_version(
            base + '/version', 'metadata-refiner',
            base + '/' + settings.REFINER_ENDPOINT.lstrip('/'))

    if enhancer:
        base = service_settings.METADATA_ENHANCER_URL.rstrip('/')
        version_dict['metadata-enhancer'] = get_service_version(
            base + '/version', 'metadata-enhancer',
            [base + '/enrich/' + path for path in enhancer_endpoints])

    return store_workflow_version(version_dict)
