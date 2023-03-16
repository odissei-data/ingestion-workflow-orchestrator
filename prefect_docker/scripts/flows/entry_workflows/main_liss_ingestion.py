import utils
from configuration.config import settings
from prefect import flow
from flows.dataset_workflows.liss_ingestion import liss_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning


@flow
def liss_ingestion_pipeline():
    version = create_ingestion_workflow_versioning(
        transformer=True,
        mapper=True,
        importer=True,
        updater=True
    )

    settings_dict = settings.LISS
    utils.workflow_executor(
        liss_metadata_ingestion,
        version,
        settings_dict
    )


if __name__ == "__main__":
    liss_ingestion_pipeline()
