from prefect import serve
from flows.entry_workflows.main_cbs_ingestion import cbs_ingestion_pipeline
from flows.entry_workflows.main_cid_ingestion import cid_ingestion_pipeline
from flows.entry_workflows.main_liss_ingestion import liss_ingestion_pipeline
from flows.entry_workflows.main_dataverse_ingestion import \
    dataverse_ingestion_pipeline

if __name__ == "__main__":
    cbs_deploy = cbs_ingestion_pipeline.to_deployment(
        name="cbs-ingestion-deployment")
    cid_deploy = cid_ingestion_pipeline.to_deployment(
        name="cid-ingestion-deployment")
    liss_deploy = liss_ingestion_pipeline.to_deployment(
        name="liss-ingestion-deployment")
    dv_deploy = dataverse_ingestion_pipeline.to_deployment(
        name="dataverse-ingestion-deployment")

    serve(cbs_deploy, cid_deploy, liss_deploy, dv_deploy)
