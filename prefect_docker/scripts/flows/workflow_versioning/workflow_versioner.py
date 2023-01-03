import os
from prefect import flow
from tasks.versioning_tasks import get_service_version

VERSION = os.getenv('VERSION')


@flow
def create_ingestion_workflow_versioning(transformer=None, mapper=None,
                                         fetcher=None, importer=None,
                                         updater=None
                                         ):
    version_dict = {'workflow_orchestrator': VERSION}

    if transformer:
        transformer_name = 'DANS-transformer-service'
        transformer = get_service_version(
            service_url='https://transformer.labs.dans.knaw.nl/',
            service_name=transformer_name,
            github_username='',
            github_repo='',
            docker_username='ekoindarto',
            image_repo='dans-transformer-service',
            endpoint='https://transformer.labs.dans.knaw.nl/'
                     'transform-xml-to-json/true'
        )
        version_dict[transformer_name] = transformer

    if mapper:
        mapper_name = 'dataverse-mapper'
        mapper = get_service_version(
            service_url='https://dataverse-mapper.labs.dans.knaw.nl/version',
            service_name=mapper_name,
            github_username='odissei-data',
            github_repo=mapper_name,
            docker_username='fjodorvr',
            image_repo=mapper_name,
            endpoint='https://dataverse-mapper.labs.dans.knaw.nl/mapper'
        )
        version_dict[mapper_name] = mapper

    if fetcher:
        fetcher_name = 'dataverse-metadata-fetcher'
        fetcher = get_service_version(
            service_url='https://dataverse-fetcher.labs.dans.knaw.nl/version',
            service_name=fetcher_name,
            github_username='odissei-data',
            github_repo=fetcher_name,
            docker_username='fjodorvr',
            image_repo=fetcher_name,
            endpoint='https://dataverse-fetcher.labs.dans.knaw.nl/'
                     'dataverse-metadata-fetcher'
        )
        version_dict[fetcher_name] = fetcher

    if importer:
        importer_name = 'dataverse-importer'
        importer = get_service_version(
            service_url='https://dataverse-importer.labs.dans.knaw.nl/version',
            service_name=importer_name,
            github_username='odissei-data',
            github_repo=importer_name,
            docker_username='fjodorvr',
            image_repo=importer_name,
            endpoint='https://dataverse-importer.labs.dans.knaw.nl/importer'
        )
        version_dict[importer_name] = importer

    if updater:
        updater_name = 'publication-date-updater'
        updater = get_service_version(
            service_url='https://dataverse-date-updater.labs.dans.knaw.nl/'
                        'version',
            service_name=updater_name,
            github_username='odissei-data',
            github_repo=updater_name,
            docker_username='fjodorvr',
            image_repo=updater_name,
            endpoint='https://dataverse-date-updater.labs.dans.knaw.nl/'
                     'publication-date-updater'
        )
        version_dict[updater_name] = updater

    return version_dict
