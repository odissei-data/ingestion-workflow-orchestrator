import argparse

from prefect import flow

from configuration.config import settings
from tasks.base_tasks import semantic_enrichment
from tasks.base_tasks import extract_doi_from_dataverse


@flow
def enrichment_ingestion_pipeline(settings_dict_name: str):
    settings_dict = getattr(settings, settings_dict_name)

    dois = extract_doi_from_dataverse(settings_dict, settings_dict.ALIAS)

    for doi in dois:
        semantic_enrichment(settings_dict, doi)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the enrichment pipeline with specified settings.")
    parser.add_argument("settings_dict_name", type=str,
                        help="Name of the settings dictionary to use.")
    args = parser.parse_args()
    enrichment_ingestion_pipeline(args.settings_dict_name)
