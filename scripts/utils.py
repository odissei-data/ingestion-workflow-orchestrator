import re
import json

import boto3
import requests
from botocore.client import BaseClient
from botocore.exceptions import ClientError
from prefect import get_run_logger
from prefect.runtime import flow_run as runtime_flow_run
from prefect.states import Failed

from configuration.config import settings


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


def workflow_executor(
        data_provider_workflow,
        version,
        settings_dict,
        minio_client
):
    """
    Executes the workflow of a give data provider for each metadata file.
    The files are retrieved from minio storage using a boto client.

    Takes workflow flow that ingests a single metadata file of a data provider
    and executes that workflow for every metadata file in the given directory.

    For Dataverse to Dataverse ingestion, the url and api key of the source
    Dataverse are required.

    :param minio_client: The client connected to minio storage.
    :param data_provider_workflow: The workflow to ingest the metadata file.
    :param version: dict containing all version info of the workflow.
    :param settings_dict: dict, containing all settings for the workflow.
    """
    logger = get_run_logger()

    paginator = minio_client.get_paginator("list_objects_v2")
    bucket = settings_dict.BUCKET_NAME
    pages = paginator.paginate(
        Bucket=bucket,
    )

    logger.info(
        f'Ingesting into Dataverse with URL: '
        f'{settings_dict.DESTINATION_DATAVERSE_URL}.'
    )

    for page in pages:
        for obj in page["Contents"]:
            file_name = obj['Key']
            object_data = minio_client.get_object(
                Bucket=bucket,
                Key=file_name
            )
            metadata = object_data['Body'].read()
            logger.info(
                f"Retrieved file: {file_name}, Size: {len(metadata)}"
            )
            data_provider_workflow(
                metadata,
                version,
                settings_dict,
                file_name,
                return_state=True
            )


def identifier_list_workflow_executor(
        data_provider_workflow,
        version,
        settings_dict,
        s3_client
):
    """
    Grabs a file called identifiers.json from the bucket
    in settings_dict.BUCKET_NAME. That json file should be made into a dict.
    Check that the dict contains a key called pids that has a list as value.
    If not return FAILED, if it does execute the data_provider_workflow
    for every pid in the list.

    :param data_provider_workflow: A function representing the data provider workflow.
    :param version: The version of the workflow to be executed.
    :param settings_dict: A dictionary containing the settings including the BUCKET_NAME.
    :param s3_client: An object representing the Boto3 S3 client to access the bucket.
    :return: 'SUCCESS' if the workflow is executed successfully, 'FAILED' otherwise.
    """
    bucket_name = settings_dict.BUCKET_NAME
    identifiers_dict = retrieve_identifiers_from_bucket(s3_client, bucket_name)
    for pid in identifiers_dict['pids']:
        data_provider_workflow(pid, version, settings_dict, return_state=True)


def retrieve_identifiers_from_bucket(s3_client, bucket_name):
    try:
        file_data = s3_client.get_object(
            Bucket=bucket_name,
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
    return identifiers_dict


def generate_flow_run_name():
    """ Generate a unique name for a flow run based on flow name and file name.

    :return: A formatted string representing the flow run name.
    """
    flow_name = runtime_flow_run.flow_name

    parameters = runtime_flow_run.parameters
    file_name = parameters["file_name"]

    return f"{flow_name}-{file_name}"


def generate_dv_flow_run_name():
    """ Generate a unique name for a flow run using the flow name
     and the dataset PID.

    :return: A formatted string representing the flow run name.
    """
    flow_name = runtime_flow_run.flow_name

    parameters = runtime_flow_run.parameters
    pid = parameters["pid"]

    return f"{flow_name}-{pid}"


def create_s3_client():
    """ Creates and returns an S3 client using the specified configuration.

    :return: botocore.client.S3: An S3 client instance.
    """
    return boto3.client(
        's3',
        endpoint_url=settings.MINIO_SERVER_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )


def failed_ingestion_hook(flow, flow_run, state):
    """ Handles failed dataset ingestion workflows.

    Handles the ingestion failure by logging information, creating a bucket
    for failed flows, and copying the failed dataset file to the bucket.

    The runtime_flow_run in this hook is the parent workflow (entry_workflow).
    The parameters of this function all belong to the sub flow that the
    parent workflow spawned (dataset_workflow).

    :param flow: The sub flow describing the dataset ingestion.
    :param flow_run: The current run of the flow for a specific dataset.
    :param state: The state of the current flow run.
    """
    logger = get_run_logger()
    settings_dict = flow_run.parameters["settings_dict"]
    file_name = flow_run.parameters["file_name"]

    s3_client = create_s3_client()
    bucket_name = f"{settings_dict['ALIAS']}-{runtime_flow_run.id}".replace(
        "_", "").lower()
    logger.info(f"bucket name: {bucket_name}")
    create_failed_flows_bucket(bucket_name, s3_client)

    s3_client.copy_object(
        Bucket=bucket_name,
        CopySource={'Bucket': settings_dict["BUCKET_NAME"], 'Key': file_name},
        Key=file_name
    )


def failed_dataverse_ingestion_hook(flow, flow_run, state):
    logger = get_run_logger()
    settings_dict = flow_run.parameters["settings_dict"]
    pid = flow_run.parameters["pid"]

    s3_client = create_s3_client()
    bucket_name = f"{settings_dict['ALIAS']}-{runtime_flow_run.id}".replace(
        "_", "").lower()
    logger.error(f"bucket name: {bucket_name}")
    create_failed_flows_bucket(bucket_name, s3_client)

    update_identifiers_json(bucket_name, "identifiers.json", pid)


def update_identifiers_json(bucket_name, object_name, failed_pid):
    s3_client = create_s3_client()
    create_identifiers_json(s3_client, bucket_name, object_name)
    identifiers_dict = retrieve_identifiers_from_bucket(s3_client, bucket_name)
    identifiers_dict['pids'].append(failed_pid)

    updated_data = json.dumps(identifiers_dict).encode('utf-8')
    s3_client.put_object(Bucket=bucket_name, Key=object_name,
                         Body=updated_data, ContentType='application/json')


def create_identifiers_json(s3_client, bucket_name, object_name):
    try:
        s3_client.head_object(Bucket=bucket_name, Key=object_name)
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == "404":
            # If identifiers.json does not exist, create it with an empty list
            empty_identifiers = {'pids': []}
            s3_client.put_object(Bucket=bucket_name, Key=object_name,
                                 Body=json.dumps(empty_identifiers),
                                 ContentType='application/json')
        else:
            raise


def create_failed_flows_bucket(bucket_name, s3_client: BaseClient):
    """ Creates a new S3 bucket for failed flows if it does not exist.

    This function is called by the failed workflow hook to create a bucket
    that stores the dataset files of all the failed sub flows of the current
    parent flow.

    This bucket creation is only done for the first failed sub flow.
    Consequent hooks will have the same bucket_name and therefore throw
    an exception on the head_bucket function that checks if the bucket exists.

    :param bucket_name: The name of the bucket to be created.
    :param s3_client: The S3 client instance.
    """
    bucket_name = bucket_name
    logger = get_run_logger()
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == "404":
            try:
                s3_client.create_bucket(Bucket=bucket_name)
                logger.error(f'Bucket created with name: {bucket_name}.')
            except Exception as e:
                logger.error(e)
        else:
            logger.error(e)
            raise


def get_most_recent_publication_date(settings_dict):
    logger = get_run_logger()

    api_endpoint = f"{settings_dict.DESTINATION_DATAVERSE_URL}/api/search"
    headers = {"X-Dataverse-key": settings_dict.DESTINATION_DATAVERSE_API_KEY,
               'Content-Type': 'application/json'}
    params = {
        'q': '*',
        'type': 'dataset',
        'subtree': f'{settings_dict.ALIAS}',
        'sort': 'date',
        'per_page': 1
    }

    response = requests.get(api_endpoint, headers=headers, params=params)

    if not response.ok:
        raise Exception(
            f'Request failed with status code {response.status_code}:'
            f' {response.text}')

    else:
        search_results = response.json()
        if search_results['data']['total_count'] > 0:
            return search_results['data']['items'][0]['published_at']
        else:
            logger.info("No datasets found in this subverse.")
            return None
