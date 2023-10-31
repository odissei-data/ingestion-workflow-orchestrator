import json
import os
import requests
from prefect import task, get_run_logger

GITHUB_USERNAME = os.getenv('GITHUB_USERNAME')
DOCKERHUB_USERNAME = os.getenv('DOCKERHUB_USERNAME')


@task
def get_service_version(service_url, service_name, github_username,
                        github_repo, docker_username, image_repo, endpoint):
    """ Creates a version dictionary for a specific service.

    This function creates a dictionary for a specific service.
    It expects the necessary information to retrieve the service version,
    GitHub repository, and Dockerhub repository.

    :return: A version dictionary detailing the version of the service.
    """

    service_version = {
        'name': service_name,
        'version': get_deployed_service_version(service_url),
        'docker-image': get_latest_image_tag_version(docker_username,
                                                     image_repo),
        'endpoint': endpoint,
    }

    github_release = get_latest_github_release_version(
        github_username, github_repo)
    if github_release:
        service_version['github-release'] = github_release

    return service_version


def get_latest_image_tag_version(docker_username, image_repo):
    """ Grabs the latest tag version of the given image.

    Searches through the list of fetched tags from the docker hub.
    Grabs the most recent tag that was added to the list.

    :param docker_username: The user who owns the repo.
    :param image_repo: The name of the image repo.
    :return: A URL that contains the latest image tag.
    """
    logger = get_run_logger()

    response = requests.get('https://registry.hub.docker.com/v2/repositories/'
                            f'{docker_username}/{image_repo}/tags')

    if not response.ok:
        logger.info(response.text)
        return None

    tags = response.json()

    latest_tag = max(tags['results'], key=lambda x: x['last_updated'])
    latest_image = f'{docker_username}/{image_repo}:{latest_tag["name"]}'

    return latest_image


def get_latest_github_release_version(github_username, github_repo):
    """ Grabs the latest GitHub release of the given GitHub repo.

    This task uses the GitHub API to fetch the latest release of a repo.

    :param github_username: The username of the owner of the repo.
    :param github_repo: The name of the GitHub repository.
    :return: URL that links to the latest release page of the repository.
    """
    logger = get_run_logger()

    response = requests.get('https://api.github.com/repos/'
                            f'{github_username}/{github_repo}/releases/latest')

    if not response.ok:
        logger.info(response.text)
        return None

    return response.json()['html_url']


def get_deployed_service_version(service_url):
    """ Returns the service version.

    Uses the version endpoint of the service to fetch the current version.

    :param service_url: The endpoint of the service that returns the version.
    :return: The service version.
    """
    logger = get_run_logger()
    response = requests.get(service_url)

    if not response.ok:
        logger.info(response.text)
        return None

    return response.json()['version']


def store_workflow_version(version_dict):
    """ Stores the workflow version dictionary.

    The workflow version dictionary is stored using the version-tracker.
    A POST request is made to store the dict, which then response with an ID.
    This ID is used to formulate a GET request that can be used to fetch
    the dictionary.

    :param version_dict: The complete version dictionary of the workflow.
    :return: A GET request.
    """
    logger = get_run_logger()
    url = 'https://version-tracker.labs.dans.knaw.nl/store'
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers,
                             data=json.dumps(version_dict))
    if not response.ok:
        logger.info(response.text)
        return None

    version_id = response.json()['id']
    return 'https://version-tracker.labs.dans.knaw.nl/retrieve/' + version_id
