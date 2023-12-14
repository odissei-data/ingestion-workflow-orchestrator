from prefect.deployments import Deployment
from flows.entry_workflows.main_cbs_ingestion import cbs_ingestion_pipeline
from flows.entry_workflows.main_cid_ingestion import cid_ingestion_pipeline
from flows.entry_workflows.main_liss_ingestion import liss_ingestion_pipeline
from flows.entry_workflows.main_dataverse_ingestion import \
    dataverse_ingestion_pipeline


def build_deployment(workflow_function, name):
    deployment = Deployment.build_from_flow(
        name=name,
        flow_name=name,
        flow=workflow_function,
        work_queue_name='default',
        load_existing=True
    )
    deployment.apply()


if __name__ == "__main__":
    build_deployment(cbs_ingestion_pipeline, "cbs-ingestion")
    build_deployment(cid_ingestion_pipeline, "cid-ingestion")
    build_deployment(dataverse_ingestion_pipeline, "dataverse-ingestion")
    build_deployment(liss_ingestion_pipeline, "liss-ingestion")
