import boto3

import utils
from configuration.config import settings
from prefect import flow
from prefect.deployments.deployments import Deployment
from flows.dataset_workflows.easy_ingestion import easy_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning


@flow
def easy_ingestion_pipeline():
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

    settings_dict = settings.EASY
    utils.workflow_executor(
        easy_metadata_ingestion,
        version,
        settings_dict,
        minio_client
    )



def build_deployment():
    deployment = Deployment.build_from_flow(
        name='easy_ingestion',
        flow_name='easy_ingestion',
        flow=easy_ingestion_pipeline,
        work_queue_name='default'
    )
    deployment.apply()

if __name__ == "__main__":
    build_deployment()
