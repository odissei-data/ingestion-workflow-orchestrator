from prefect import flow

from flows.dataset_workflows.dataverse_nl_ingestion import \
    dataverse_nl_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning
import utils


@flow
def dataverse_nl_ingestion_pipeline(
        source_dataverse_url,
        source_dataverse_api_key,
        metadata_directory,
        destination_dataverse_alias,
):
    """
    Ingestion pipeline dedicated to dataverse.nl workflow.

    :param source_dataverse_url: string, url to source dataverse
    :param source_dataverse_api_key: string, api key for source dataverse
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
        source_dataverse_url=source_dataverse_url,
        source_dataverse_api_key=source_dataverse_api_key
    )


def test_ingestion():
    from config import settings

    dataverse_nl_ingestion_pipeline(
        settings.DATAVERSE_NL_SOURCE_DATAVERSE_URL,
        settings.RESEARCH_DATA_METADATA_DIRECTORY,
        settings.RESEARCH_DATA_DATAVERSE_ALIAS
    )


if __name__ == "__main__":
    # dataverse_nl_ingestion_pipeline()
    test_ingestion()
