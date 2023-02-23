import utils
from config import settings
from prefect import flow
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

    utils.workflow_executor(
        easy_metadata_ingestion,
        settings.EASY_METADATA_DIRECTORY,
        version,
        settings.EASY_DATAVERSE_ALIAS
    )


if __name__ == "__main__":
    easy_ingestion_pipeline()
