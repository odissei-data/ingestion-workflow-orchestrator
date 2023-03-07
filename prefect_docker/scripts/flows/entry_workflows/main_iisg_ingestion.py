import utils
from configuration.config import settings
from prefect import flow

from flows.dataset_workflows.iisg_ingestion import iisg_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning


@flow
def iisg_ingestion_pipeline():
    version = create_ingestion_workflow_versioning(
        transformer=True,
        fetcher=True,
        importer=True,
        updater=True
    )

    settings_dict = settings.IISG
    utils.workflow_executor(
        iisg_metadata_ingestion,
        version,
        settings_dict
    )


if __name__ == "__main__":
    iisg_ingestion_pipeline()
