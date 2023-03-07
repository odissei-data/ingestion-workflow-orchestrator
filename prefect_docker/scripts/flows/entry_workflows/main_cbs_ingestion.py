from configuration.config import settings
from prefect import flow
import utils
from flows.dataset_workflows.cbs_ingestion import cbs_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning


@flow
def cbs_ingestion_pipeline():
    version = create_ingestion_workflow_versioning(
        transformer=True,
        mapper=True,
        minter=True,
        importer=True,
        updater=True
    )

    settings_dict = settings.CBS
    utils.workflow_executor(
        cbs_metadata_ingestion,
        version,
        settings_dict
    )


if __name__ == "__main__":
    cbs_ingestion_pipeline()
