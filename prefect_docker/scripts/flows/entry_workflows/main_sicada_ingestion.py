import argparse

import utils
from configuration.config import settings
from prefect import flow

from flows.dataset_workflows.sicada_ingestion import sicada_metadata_ingestion
from flows.workflow_versioning.workflow_versioner import \
    create_ingestion_workflow_versioning


@flow
def sicada_ingestion_pipeline(settings_dict_name):
    """
    Ingestion pipeline dedicated to sicada workflow.

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
        sicada_metadata_ingestion,
        version,
        settings_dict
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingestion pipeline for Sicada workflow."
    )
    parser.add_argument(
        "settings_dict_name", help="Name of the target subverse."
    )
    args = parser.parse_args()
    sicada_ingestion_pipeline(args.settings_dict_name)
