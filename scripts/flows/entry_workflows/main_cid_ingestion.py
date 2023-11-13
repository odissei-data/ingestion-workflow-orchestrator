import boto3
import utils
from prefect import flow
from configuration.config import settings
from flows.dataset_workflows.cid_ingestion import cid_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning


@flow
def cid_ingestion_pipeline(target_url: str = None, target_key: str = None):
    """

    :param target_url:
    :param target_key:
    :return:
    """

    settings_dict = settings.CID

    if target_url:
        settings_dict.DESTINATION_DATAVERSE_URL = target_url

    if target_key:
        settings_dict.DESTINATION_DATAVERSE_API_KEY = target_key

    version = create_ingestion_workflow_versioning(
        transformer=True,
        mapper=True,
        importer=True,
        updater=True
    )

    minio_client = boto3.client(
        's3',
        endpoint_url=settings.MINIO_SERVER_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )

    # harvest_metadata(
    #     settings_dict.BUCKET_NAME,
    #     "start_cid_harvest"
    # )

    utils.workflow_executor(
        cid_metadata_ingestion,
        version,
        settings_dict,
        minio_client
    )


if __name__ == "__main__":
    cid_ingestion_pipeline("https://portal.alpha.odissei.nl",
                           "a22cb0b4-af35-4b03-a123-36b9e63f5eda")