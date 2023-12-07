import asyncio
import re
import json
import traceback

import httpx
import tenacity as tenacity
from botocore.exceptions import ClientError
from prefect import get_run_logger
from prefect.states import Failed


def retrieve_license_name(license_string):
    dataset_lic = ''
    if re.search(r'creativecommons', license_string):
        if re.search(r'/by/4\.0', license_string):
            dataset_lic = "CC BY 4.0"
        elif re.search(r'/by-nc/4\.0', license_string):
            dataset_lic = "CC BY-NC 4.0"
        elif re.search(r'/by-sa/4\.0', license_string):
            dataset_lic = "CC BY-SA 4.0"
        elif re.search(r'/by-nc-sa/4\.0', license_string):
            dataset_lic = "CC BY-NC-SA 4.0"
        elif re.search(r'zero/1\.0', license_string):
            dataset_lic = "CC0 1.0"
    elif re.search(r'DANSLicence', license_string):
        dataset_lic = "DANS Licence"
    return dataset_lic


def is_lower_level_liss_study(metadata):
    logger = get_run_logger()
    title = metadata['datasetVersion']['metadataBlocks']['citation'][
        'fields'][0]['value']
    logger.info(f"Title is {title}")
    square_bracket_amount = title.count('>')
    if square_bracket_amount == 0:
        logger.info('no square brackets')
        return False, title
    if square_bracket_amount == 1:
        liss_match = re.search(r'L[iI]SS [Pp]anel', title)
        immigrant_match = re.search(r'Immigrant [Pp]anel', title)
        if liss_match or immigrant_match:
            if liss_match:
                logger.info("Matched on liss panel")
                return False, title
            if immigrant_match:
                logger.info("Matched on immigrant panel")
                return False, title
        else:
            return True, title
    if square_bracket_amount >= 2:
        return True, title


async def workflow_executor(data_provider_workflow, version, settings_dict,
                            minio_client, max_concurrent=8):
    """ Creates a workflow for each object retrieved from minio.

    The workflow executor uses asyncio to concurrently run ingestion workflows.
    It first retrieves all datasets from s3 storage using the minio client.
    It creates a workflow for each dataset it retrieved. A workflow refines
    and enriches the metadata after which it ingests it in to Dataverse.

    :param data_provider_workflow: The workflow ingestion function.
    :param version: A dictionary describing the version information.
    :param settings_dict: A dictionary that stores the settings for the wf.
    :param minio_client: The client for the s3 storage.
    :param max_concurrent: The maximum amount of concurrent workflows.
    """
    logger = get_run_logger()

    logger.info(
        f'Ingesting into Dataverse with URL: '
        f'{settings_dict.DESTINATION_DATAVERSE_URL}.')

    paginator = minio_client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=settings_dict.BUCKET_NAME)

    sem = asyncio.Semaphore(max_concurrent)
    tasks = []

    for page in pages:
        for obj in page["Contents"]:
            tasks.append(
                execute_workflow(obj, sem, minio_client,
                                 data_provider_workflow,
                                 version, settings_dict))

    await asyncio.gather(*tasks)


async def execute_workflow(obj, sem, minio_client, data_provider_workflow,
                           version, settings_dict):
    """ A gatherable task executing a workflow.

    :param obj: The object retrieved from s3 storage containing the metadata.
    :param sem: The semaphore that determines the max concurrent workflows.
    :param minio_client: The client for s3 storage.
    :param data_provider_workflow: The ingestion workflow function.
    :param version: The dictionary containing version information.
    :param settings_dict: Dictionary containing settings.
    :return: 'SUCCESS' if the workflow is successful, 'FAILED' otherwise.
    """
    logger = get_run_logger()

    async with sem:
        object_data = await asyncio.to_thread(
            minio_client.get_object,
            Bucket=settings_dict.BUCKET_NAME,
            Key=obj['Key']
        )

        metadata = object_data['Body'].read()
        logger.info(f"Retrieved file: {obj['Key']}, Size: {len(metadata)}")
        await data_provider_workflow(metadata, version, settings_dict,
                                     return_state=True)


async def identifier_list_workflow_executor(
        data_provider_workflow,
        version,
        settings_dict,
        s3_client,
        max_concurrent=8
):
    """
    Grabs a file called identifiers.json from the bucket
    in settings_dict.BUCKET_NAME. That json file should be made into a dict.
    Check that the dict contains a key called pids that has a list as value.
    If not return FAILED, if it does execute the data_provider_workflow
    for every pid in the list. The workflows are executed concurrently.

    :param data_provider_workflow: The workflow ingestion function.
    :param version: The version of the workflow to be executed.
    :param settings_dict: Dictionary containing settings including BUCKET_NAME.
    :param s3_client: An object representing the Boto3 S3 client.
    :param max_concurrent: Max amount of concurrent workflow.
    :return: 'SUCCESS' if the workflow is successful, 'FAILED' otherwise.
    """
    logger = get_run_logger()

    logger.info(
        f'Ingesting into Dataverse with URL: '
        f'{settings_dict.DESTINATION_DATAVERSE_URL}.')
    try:
        file_data = s3_client.get_object(
            Bucket=settings_dict.BUCKET_NAME,
            Key='identifiers.json')['Body'].read()
        identifiers_dict = json.loads(file_data)

    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            return Failed(message="identifiers.json not found in the bucket.")
        else:
            return Failed(
                message="Error accessing identifiers.json from the bucket.")

    except json.JSONDecodeError as e:
        return Failed(message="identifiers.json is not in valid JSON format.")

    if 'pids' not in identifiers_dict or not isinstance(
            identifiers_dict['pids'], list):
        return Failed(
            message=f"identifiers.json does not contain the pids key or it"
                    f" does not have a list as value.")

    sem = asyncio.Semaphore(max_concurrent)
    tasks = []
    for pid in identifiers_dict['pids']:
        tasks.append(process_pid(pid, sem, data_provider_workflow, version,
                                 settings_dict))
    await asyncio.gather(*tasks)


async def process_pid(pid, sem, data_provider_workflow, version,
                      settings_dict):
    async with sem:
        await data_provider_workflow(pid, version, settings_dict,
                                     return_state=True)


@tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=3, max=30))
async def async_http_request_handler(url: str, headers: dict,
                                     data: dict = None):
    """ Handles async POST requests using httpx, with retries on >= 400.

    :param url: Request url.
    :param headers: Request headers.
    :param data: Request data.
    :return: Response as a dict.
    """

    logger = get_run_logger()
    data = json.dumps(data)
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, headers=headers, data=data)
            if resp.status_code >= 400:
                logger.info(f"The request got a response code >=400")
                resp.raise_for_status()
        except httpx.HTTPError as ex:
            logger.info(f"POST request returned error: {ex}.")
            logger.info(traceback.print_exc())
            if resp is not None and resp.text:
                logger.info(f"With error text: {resp.text}")
            raise

    return resp.json()
