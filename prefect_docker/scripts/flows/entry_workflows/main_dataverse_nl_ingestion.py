import argparse

from prefect import flow

from configuration.config import settings
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

    settings_dict = getattr(settings, settings_dict_name)
    utils.workflow_executor(
        dataverse_nl_metadata_ingestion,
        version,
        settings_dict,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingestion pipeline for DataverseNL workflow.")
    parser.add_argument("settings_dict_name",
                        help="Name of the target subverse.")
    args = parser.parse_args()

    dataverse_nl_ingestion_pipeline(args.settings_dict_name)
