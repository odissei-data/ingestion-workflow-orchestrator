import os
import re


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

    Takes workflow flow that ingests a single metadata file of a data provider
    and executes that workflow for every metadata file in the given directory.

    For Dataverse to Dataverse ingestion, the url and api key of the source
    Dataverse are required.

    :param data_provider_workflow: The workflow to ingest the metadata file.
    :param version: dict containing all version info of the workflow.
    :param settings_dict: dict, containing all settings for the workflow.
    :return: None
    """

    bucket_name = 'harvested-metadata'
    object_prefix = settings_dict.METADATA_DIRECTORY

    response = minio_client.list_objects(Bucket=bucket_name,
                                         Prefix=object_prefix)

    for obj in response.get('Contents', []):
        object_data = minio_client.get_object(Bucket=bucket_name,
                                              Key=obj['Key'])
        xml_metadata = object_data['Body'].read()
        data_provider_workflow(xml_metadata, version, settings_dict,
                               return_state=True)
