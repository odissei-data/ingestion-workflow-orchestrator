from types import SimpleNamespace

import utils

SETTINGS = SimpleNamespace(PROVIDER_NAME='DataverseNL')


def test_harvest_source():
    source = utils.metadata_source(
        SETTINGS, 'OAI-PMH', True,
        endpoint='https://dataverse.nl/oai', oai_set='Tilburg_Social_Sciences')
    assert source.pop('harvested-on')
    assert source == {'provider': 'DataverseNL', 'method': 'OAI-PMH',
                      'endpoint': 'https://dataverse.nl/oai',
                      'set': 'Tilburg_Social_Sciences'}


def test_source_without_a_harvest():
    assert utils.metadata_source(SETTINGS, 'metadata delivery', False) == {
        'provider': 'DataverseNL', 'method': 'metadata delivery',
        'harvested-on': None}
