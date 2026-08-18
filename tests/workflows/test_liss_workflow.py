import pytest
from prefect.logging import disable_run_logger

from utils import is_lower_level_liss_study


def _metadata(title):
    return {
        'datasetVersion': {
            'metadataBlocks': {
                'citation': {'fields': [{'typeName': 'title',
                                         'value': title}]}
            }
        }
    }


def _is_lower(title):
    with disable_run_logger():
        return is_lower_level_liss_study(_metadata(title))[0]


@pytest.mark.parametrize('title', [
    'Neighbourhood perceptions',
    'LISS panel > Neighbourhood perceptions',
    'LISS Panel > Neighbourhood perceptions',
    'Immigrant panel > Retrospective Childhood',
])
def test_top_level_studies_are_kept(title):
    assert _is_lower(title) is False


@pytest.mark.parametrize('title', [
    'Some other archive > A study',
    'LISS panel > A study > Wave 1',
])
def test_lower_level_studies_are_skipped(title):
    assert _is_lower(title) is True


@pytest.mark.parametrize('title', [
    'LISS Data Archive > Neighbourhood perceptions',
    'LISS Data Archive > European Values Study (LISS panel version)',
])
def test_liss_data_archive_is_a_top_level_study(title):
    """ The source renamed the top-level prefix from "LISS panel" to
    "LISS Data Archive". Both name the same level and must be ingested.
    """
    assert _is_lower(title) is False
