import os
from prefect import flow
from flows.cbs_ingestion import cbs_metadata_ingestion
from flows.easy_ingestion import easy_metadata_ingestion
from flows.liss_ingestion import liss_metadata_ingestion

DATA_PROVIDER = os.getenv('DATA_PROVIDER')


@flow
def ingestion_pipeline():
    metadata_directory = f"/{DATA_PROVIDER}-metadata"
    files = [f for f in os.listdir(metadata_directory) if
             not f.startswith('.')]
    for filename in files:
        file_path = os.path.join(metadata_directory, filename)
        if os.path.isfile(file_path):
            # Can I avoid this switch
            # if I pass the ingestion function as a parameter?
            if DATA_PROVIDER == 'cbs':
                cbs_metadata_ingestion(file_path, return_state=True)
            elif DATA_PROVIDER == 'easy':
                easy_metadata_ingestion(file_path, return_state=True)
            elif DATA_PROVIDER == 'liss':
                liss_metadata_ingestion(file_path, return_state=True)


if __name__ == "__main__":
    ingestion_pipeline()
