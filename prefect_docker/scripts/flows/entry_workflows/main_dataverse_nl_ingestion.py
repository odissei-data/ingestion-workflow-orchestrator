from prefect import flow

from flows.dataset_workflows.dataverse_nl_ingestion import \
    dataverse_nl_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning
import utils


@flow
def dataverse_nl_ingestion_pipeline(settings_dict_name):
    """
    Ingestion pipeline dedicated to dataverse.nl workflow.

    :param settings_dict_name: string, name of the settings you wish to use
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
        version=version,
        settings_dict_name=settings_dict_name,
    )


def test_ingestion():
    dataverse_nl_ingestion_pipeline("RESEARCH_DATA")


if __name__ == "__main__":
    # dataverse_nl_ingestion_pipeline()
    test_ingestion()
