import boto3

from configuration.config import settings
from prefect import flow
import utils
from flows.dataset_workflows.enrichment import metadata_enrichment
from tasks.base_tasks import semantic_enrichment
from tasks.base_tasks import extract_doi_from_dataverse


@flow
def enrichment_ingestion_pipeline():
    settings_dict = settings.CBS

    dois = extract_doi_from_dataverse(settings_dict)

    for doi in dois:
        response = semantic_enrichment(settings_dict, doi)
        print(response)


if __name__ == "__main__":
    enrichment_ingestion_pipeline()
