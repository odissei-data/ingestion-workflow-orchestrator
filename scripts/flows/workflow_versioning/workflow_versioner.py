import os
from datetime import datetime

from prefect import flow
from tasks.versioning_tasks import get_service_version, store_workflow_version

VERSION = os.getenv('VERSION')


@flow
def create_ingestion_workflow_versioning(
        transformer: bool = False,
        mapper: bool = False,
        fetcher: bool = False,
        minter: bool = False,
        refiner: bool = False,
        enhancer: bool = False,
        importer: bool = False,
        updater: bool = False,
        settings=None
):
    """ Creates a version dictionary detailing a specific ingestion workflow.

    The different workflows all use a set of services that have their own
    versioning information. This flow creates a dictionary with up-to-date
    information on the services passed as parameters. All parameters are bools
    indicating if the service in question was used.

    :return: A dictionary with all versioning information for a workflow.
    """

    version_dict = {'workflow_orchestrator': VERSION}

    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%d-%m-%Y %H:%M:%S")
    version_dict['created_on'] = formatted_datetime

    if transformer:
        transformer_name = 'DANS-transformer-service'
        transformer = get_service_version(
            service_url='https://transformer.labs.dansdemo.nl/',
            service_name=transformer_name,
            github_username='',
            github_repo='',
            docker_username='ekoindarto',
            image_repo='dans-transformer-service',
            endpoint='https://transformer.labs.dansdemo.nl/'
                     'transform-xml-to-json/true'
        )
        version_dict[transformer_name] = transformer

    if mapper:
        mapper_name = 'dataverse-mapper'
        mapper = get_service_version(
            service_url='https://dataverse-mapper.labs.dansdemo.nl/version',
            service_name=mapper_name,
            github_username='odissei-data',
            github_repo=mapper_name,
            docker_username='fjodorvr',
            image_repo=mapper_name,
            endpoint='https://dataverse-mapper.labs.dansdemo.nl/mapper'
        )
        version_dict[mapper_name] = mapper

    if fetcher:
        fetcher_name = 'dataverse-metadata-fetcher'
        fetcher = get_service_version(
            service_url='https://dataverse-fetcher.labs.dansdemo.nl/version',
            service_name=fetcher_name,
            github_username='odissei-data',
            github_repo=fetcher_name,
            docker_username='fjodorvr',
            image_repo=fetcher_name,
            endpoint='https://dataverse-fetcher.labs.dansdemo.nl/'
                     'dataverse-metadata-fetcher'
        )
        version_dict[fetcher_name] = fetcher

    if minter:
        minter_name = 'datacite-minter'
        minter = get_service_version(
            service_url='https://dataciteminter.labs.dansdemo.nl/',
            service_name=minter_name,
            github_username='',
            github_repo='',
            docker_username='ekoindarto',
            image_repo='submitmd2dc-service',
            endpoint='https://dataciteminter.labs.dansdemo.nl/'
                     'submit-to-datacite/register'
        )
        version_dict[minter_name] = minter

    if importer:
        importer_name = 'dataverse-importer'
        importer = get_service_version(
            service_url='https://dataverse-importer.labs.dansdemo.nl/version',
            service_name=importer_name,
            github_username='odissei-data',
            github_repo=importer_name,
            docker_username='fjodorvr',
            image_repo=importer_name,
            endpoint='https://dataverse-importer.labs.dansdemo.nl/importer'
        )
        version_dict[importer_name] = importer

    if updater:
        updater_name = 'publication-date-updater'
        updater = get_service_version(
            service_url='https://dataverse-date-updater.labs.dansdemo.nl/'
                        'version',
            service_name=updater_name,
            github_username='odissei-data',
            github_repo=updater_name,
            docker_username='fjodorvr',
            image_repo=updater_name,
            endpoint='https://dataverse-date-updater.labs.dansdemo.nl/'
                     'publication-date-updater'
        )
        version_dict[updater_name] = updater

    if refiner:
        refiner_name = 'metadata-refiner'
        refiner = get_service_version(
            service_url='https://metadata-refiner.labs.dansdemo.nl/version',
            service_name=refiner_name,
            github_username='odissei-data',
            github_repo=refiner_name,
            docker_username='fjodorvr',
            image_repo=refiner_name,
            endpoint='https://metadata-refiner.labs.dansdemo.nl'
                     + settings.REFINER_ENDPOINT
        )
        version_dict[refiner_name] = refiner

    if enhancer:
        enhancer_name = 'metadata-enhancer'
        enhancer = get_service_version(
            service_url='https://metadata-enhancer.labs.dansdemo.nl/version',
            service_name=enhancer_name,
            github_username='odissei-data',
            github_repo=enhancer_name,
            docker_username='fjodorvr',
            image_repo=enhancer_name,
            endpoint=[
                'https://metadata-enhancer.labs.dansdemo.nl/'
                'dataverse-ELSST-enhancer'
                'https://metadata-enhancer.labs.dansdemo.nl/'
                'dataverse-variable-enhancer'
                'https://metadata-enhancer.labs.dansdemo.nl/'
                'dataverse-frequency-enhancer'
            ]
        )
        version_dict[enhancer_name] = enhancer

    version = store_workflow_version(version_dict)

    return version
