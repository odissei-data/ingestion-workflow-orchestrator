import boto3

from configuration.config import settings
from prefect import flow
import utils
from flows.dataset_workflows.cbs_ingestion import cbs_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning


@flow
def cbs_ingestion_pipeline():
    settings_dict = settings.CBS

    version = create_ingestion_workflow_versioning(
        transformer=True,
        mapper=True,
        minter=True,
        importer=True,
        updater=True,
        refiner=True,
        settings=settings.CBS
    )

    minio_client = boto3.client(
        's3',
        endpoint_url=settings.MINIO_SERVER_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )

    utils.workflow_executor(
        cbs_metadata_ingestion,
        version,
        settings_dict,
        minio_client
    )


if __name__ == "__main__":
    cbs_ingestion_pipeline()
