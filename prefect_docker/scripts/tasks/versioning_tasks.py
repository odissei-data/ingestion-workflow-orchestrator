import os
import requests
from prefect import task, get_run_logger

GITHUB_USERNAME = os.getenv('GITHUB_USERNAME')
DOCKERHUB_USERNAME = os.getenv('DOCKERHUB_USERNAME')


@task
def get_service_version(service_url, service_name, github_username,
                        github_repo, docker_username, image_repo, endpoint):
    service_version = {
            'name': service_name,
            'version': get_deployed_service_version(service_url),
            'github-release': get_latest_github_release_version(
                github_username, github_repo),
            'docker-image': get_latest_image_tag_version(docker_username,
                                                         image_repo),
            'endpoint': endpoint,
        }

    return service_version


def get_latest_image_tag_version(docker_username, image_repo):
    logger = get_run_logger()

    response = requests.get('https://registry.hub.docker.com/v2/repositories/'
                            f'{docker_username}/{image_repo}/tags')

    if not response.ok:
        logger.info(response.json())
        return None

    tags = response.json()

    latest_tag = max(tags['results'], key=lambda x: x['last_updated'])
    latest_tag_link = 'https://hub.docker.com/r/' \
                      f'{DOCKERHUB_USERNAME}/{image_repo}/tags/' \
                      f'{latest_tag["name"]}'

    return latest_tag_link


def get_latest_github_release_version(github_username, github_repo):
    logger = get_run_logger()

    response = requests.get('https://api.github.com/repos/'
                            f'{github_username}/{github_repo}/releases/latest')

    if not response.ok:
        logger.info(response.json())
        return None

    return response.json()['html_url']


def get_deployed_service_version(service_url):
    logger = get_run_logger()
    response = requests.get(service_url)

    if not response.ok:
        logger.info(response.json())
        return None

    return response.json()['version']
