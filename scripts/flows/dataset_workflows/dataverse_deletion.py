from prefect import flow
from prefect.states import Failed, Completed

from tasks.base_tasks import dataverse_dataset_check_status, \
    delete_dataset
from utils import generate_dv_flow_run_name, failed_dataverse_deletion_hook


@flow(name="Deleting Dataverse metadata",
      flow_run_name=generate_dv_flow_run_name,
      on_failure=[failed_dataverse_deletion_hook])
def dataverse_metadata_deletion(pid, settings_dict):
    """
    Deletion flow for Dataverse to dataverse ingestion.

    :param pid: pid of the dataset.
    :param settings_dict: dict, contains settings for the current workflow.
    :return: prefect.server.schemas.states Failed or Completed.
    """
    dv_response_status = dataverse_dataset_check_status(
        pid,
        settings_dict.DESTINATION_DATAVERSE_URL)

    if not dv_response_status:
        return Failed(message=f'No response from {pid}.')

    if dv_response_status in (404, 403):
        response = delete_dataset(pid, settings_dict)
        if not response:
            return Failed(message=f'Unable to delete dataset: {pid}.')

        return Completed(message=pid + 'deleted successfully.')

    # If the dataset is active: 200, it will not be deleted.
    return Failed(message=f'{pid} will not deleted. Dataset is active.')
