import os
import utils
from prefect import flow
from flows.dataset_workflows.iisg_ingestion import iisg_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning

IISG_METADATA_DIRECTORY = os.getenv('IISG_METADATA_DIRECTORY')


@flow
def iisg_ingestion_pipeline():
    version = create_ingestion_workflow_versioning(
        transformer=True,
        fetcher=True,
        importer=True,
        updater=True
    )

    utils.workflow_executor(
        iisg_metadata_ingestion,
        "/local-metadata/iisg-metadata",
        version,
        "michielz"
    )


if __name__ == "__main__":
    iisg_ingestion_pipeline()