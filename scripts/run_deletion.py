import argparse

from configuration.config import settings
# from flows.entry_workflows.main_cbs_deletion import cbs_deletion_pipeline
# from flows.entry_workflows.main_cid_deletion import cid_deletion_pipeline

from flows.entry_workflows.main_dataverse_deletion import dataverse_deletion_pipeline

# from flows.entry_workflows.main_liss_deletion import liss_deletion_pipeline


def run_deletion():
    """ Allows Deletion workflows to be executed from the command line.

    Prompts a user to provide a data provider, optionally a target key and url.
    The user is then prompted to check the target url.
    """

    data_providers = [
        'TWENTE', 'DELFT', 'AVANS', 'FONTYS', 'GRONINGEN', 'HANZE', 'HR',
        'LEIDEN', 'MAASTRICHT', 'TILBURG', 'TRIMBOS', 'UMCU', 'UTRECHT', 'VU',
        'DANS', 'CBS', 'LISS', 'HSN', 'CID']

    parser = argparse.ArgumentParser(description="Run deletion pipeline.")
    parser.add_argument('--data_provider', type=str,
                        help=f"Provider of the dataset metadata that will be "
                             f"deleted in to the target. Options: "
                             f"{data_providers}")
    parser.add_argument('--target_url', type=str, default=None,
                        help='Target URL')
    parser.add_argument('--target_key', type=str, default=None,
                        help='Target key')
    parser.add_argument('--do_harvest', type=str, default="",
                        help='Bool that states if the metadata will'
                             ' be harvested.')
    args = parser.parse_args()

    print(f"args: {args}")
    # do_harvest = args.do_harvest.lower() == 'true'
    do_harvest = True
    # provider_mapping = {
    #     'CBS': cbs_deletion_pipeline,
    #     'LISS': liss_deletion_pipeline,
    #     'CID': cid_deletion_pipeline,
    # }

    if args.data_provider not in data_providers:
        print(f"Invalid data provider specified, please choose from this list:"
              f" {data_providers}")
        return

    if args.data_provider in provider_mapping:
        deletion_function = provider_mapping[args.data_provider]
        settings_dict = getattr(settings, args.data_provider)
        target_url = get_target_url(args.target_url, settings_dict)
        dataverse_deletion_pipeline(target_url, args.target_key, do_harvest)

    else:
        settings_dict = getattr(settings, args.data_provider)
        target_url = get_target_url(args.target_url, settings_dict)
        dataverse_deletion_pipeline(args.data_provider, target_url, args.target_key, do_harvest)


def prompt_for_confirmation(target_url):
    print("Current target configuration:")
    print(f"Target URL: {target_url}")
    confirmation = input(
        "Do you want to proceed with this configuration? (yes/no): ").lower()
    return confirmation == 'yes'


def get_target_url(target_url, settings_dict):
    if not target_url:
        return settings_dict.DESTINATION_DATAVERSE_URL
    else:
        return target_url


if __name__ == "__main__":
    run_deletion()
