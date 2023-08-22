import re
import json

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
    title = metadata['datasetVersion']['metadataBlocks']['citation'][
        'fields'][0]['value']
    print("Title is", title)
    square_bracket_amount = title.count('>')
    if square_bracket_amount == 0:
        print('no square brackets')
        return False, title
    if square_bracket_amount == 1:
        liss_match = re.search(r'L[iI]SS [Pp]anel', title)
        immigrant_match = re.search(r'Immigrant [Pp]anel', title)
        if liss_match or immigrant_match:
            if liss_match:
                print("Matched on liss panel")
                return False, title
            if immigrant_match:
                print("Matched on immigrant panel")
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
            object_data = minio_client.get_object(
                Bucket=bucket,
                Key=obj['Key']
            )
            xml_metadata = object_data['Body'].read()
            logger.info(
                f"Retrieved file: {obj['Key']}, Size: {len(xml_metadata)}"
            )
            data_provider_workflow(
                xml_metadata,
                version,
                settings_dict,
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

    :param data_provider_workflow: A function representing the data provider workflow
    :param version: The version of the workflow to be executed
    :param settings_dict: A dictionary containing the settings including the BUCKET_NAME
    :param s3_client: An object representing the Boto3 S3 client to access the bucket
    :return: 'SUCCESS' if the workflow is executed successfully, 'FAILED' otherwise
    """

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
    print(identifiers_dict)
    for pid in identifiers_dict['pids']:
        data_provider_workflow(pid, version, settings_dict, return_state=True)
