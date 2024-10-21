from pathlib import Path

from flows.entry_workflows.main_cbs_ingestion import cbs_ingestion_pipeline
from flows.entry_workflows.main_cid_ingestion import cid_ingestion_pipeline
from flows.entry_workflows.main_liss_ingestion import liss_ingestion_pipeline
from flows.entry_workflows.main_dataverse_ingestion import \
    dataverse_ingestion_pipeline


def build_deployment(workflow_function, entrypoint_name, name):
    workflow_function.from_source(
        source="/app/scripts/flows/entry_workflows/",
        entrypoint=f"{entrypoint_name}:{name}",
    ).deploy(
        name=name,
        work_pool_name='default',
    )


if __name__ == "__main__":
    build_deployment(cbs_ingestion_pipeline, "main_cbs_ingestion.py",
                     "cbs_ingestion_pipeline")
    build_deployment(cid_ingestion_pipeline, "main_cid_ingestion.py",
                     "cid_ingestion_pipeline")
    build_deployment(dataverse_ingestion_pipeline,
                     "main_dataverse_ingestion.py",
                     "dataverse_ingestion_pipeline")
    build_deployment(liss_ingestion_pipeline, "main_liss_ingestion.py",
                     "liss_ingestion_pipeline")
