from prefect import flow

from flows.dataset_workflows.dataverse_nl_ingestion import \
    dataverse_nl_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning
import utils


@flow
def dataverse_to_dataverse_ingestion_pipeline(
        source_dataverse_url,
        metadata_directory,
        destination_dataverse_alias
):
    """
    This ingestion pipeline can only be used when moving metadata from one
    Dataverse to another Dataverse.

    Metadata is assumed to be available in the provided metadata directory.
    This pipeline does not harvest!

    :param source_dataverse_url: string, url to source dataverse
    :param metadata_directory: string, name of metadata directory
    :param destination_dataverse_alias: string, alias used by destination
    dataverse

    :return: None
    """
    version = create_ingestion_workflow_versioning(
        transformer=True,
        fetcher=True,
        importer=True,
        updater=True
    )

    utils.workflow_executor(
        data_provider_workflow=dataverse_nl_metadata_ingestion,
        metadata_directory=metadata_directory,
        version=version,
        alias=destination_dataverse_alias,
        source_dataverse_url=source_dataverse_url
    )
