from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from prefect.logging import disable_run_logger

from configuration import config
from flows.workflow_versioning import workflow_versioner
from tasks import versioning_tasks


def _record(monkeypatch, body):
    get = Mock(return_value=Mock(json=Mock(return_value=body), text=str(body)))
    monkeypatch.setattr(versioning_tasks.requests, 'get', get)
    with disable_run_logger():
        record = versioning_tasks.get_service_version.fn(
            'http://mapper:8082/health', 'dataverse-mapper',
            'http://mapper:8082/mapper')
    get.assert_called_once_with('http://mapper:8082/health', timeout=30)
    return record


def test_version_and_image_come_from_the_health_route(monkeypatch):
    record = _record(monkeypatch, {
        'status': 'ok', 'version': 'v2.1.0',
        'image': 'ghcr.io/odissei-data/dataverse-mapper:v2.1.0',
        'source': 'https://github.com/odissei-data/dataverse-mapper/releases/tag/v2.1.0'})
    assert record == {
        'name': 'dataverse-mapper',
        'version': 'v2.1.0',
        'docker-image': 'ghcr.io/odissei-data/dataverse-mapper:v2.1.0',
        'source-code': 'https://github.com/odissei-data/dataverse-mapper/releases/tag/v2.1.0',
        'endpoint': 'http://mapper:8082/mapper',
    }


def test_openapi_version_has_no_image(monkeypatch):
    record = _record(monkeypatch, {'info': {'version': '0.3.0'}})
    assert record['version'] == '0.3.0'
    assert record['docker-image'] is None
    assert record['source-code'] is None


def test_missing_version_fails(monkeypatch):
    with pytest.raises(ValueError):
        _record(monkeypatch, {'status': 'ok'})


def test_endpoints_are_recorded_by_their_public_url(monkeypatch):
    monkeypatch.setattr(config, 'settings', {
        'PUBLIC_URLS': {'http://mapper:8082': 'https://mapper.example.org'}})
    record = _record(monkeypatch, {'status': 'ok', 'version': 'v2.1.0'})
    assert record['endpoint'] == 'https://mapper.example.org/mapper'


def test_mapping_version_comes_from_mapping_versions(tmp_path):
    (tmp_path / 'mapping-versions').write_text('base v1.0.0\ncbs v1.2.0\n')
    assert versioning_tasks.get_mapping_version(
        tmp_path / 'mappings' / 'cbs-mapping.json') == (
        'https://github.com/odissei-data/mappings/tree/cbs/v1.2.0')


def _workflow_version(monkeypatch, **services):
    monkeypatch.setattr(workflow_versioner, 'service_settings', SimpleNamespace(
        DANS_TRANSFORMER_SERVICE='http://transformer',
        DATAVERSE_MAPPER_URL='http://mapper'))
    monkeypatch.setattr(workflow_versioner, 'get_service_version',
                        lambda url, name, endpoint: {'name': name})
    monkeypatch.setattr(workflow_versioner, 'get_mapping_version',
                        lambda path: 'tag')
    monkeypatch.setattr(workflow_versioner, 'store_workflow_version',
                        lambda version: version)
    return workflow_versioner.create_ingestion_workflow_versioning.fn(
        settings=SimpleNamespace(MAPPING_FILE_PATH='mapping.json'), **services)


def test_transformer_without_mapper_records_the_mapping(monkeypatch):
    version = _workflow_version(monkeypatch, transformer=True)
    assert version['DANS-transformer-service']['mapping'] == 'tag'


def test_transformer_with_mapper_records_the_mapping_on_the_mapper(monkeypatch):
    version = _workflow_version(monkeypatch, transformer=True, mapper=True)
    assert 'mapping' not in version['DANS-transformer-service']
    assert version['dataverse-mapper']['mapping'] == 'tag'


def test_orchestrator_source_comes_from_the_build(monkeypatch):
    monkeypatch.setenv('APP_SOURCE', 'https://github.com/odissei-data/'
                       'ingestion-workflow-orchestrator/releases/tag/v1.2.3')
    version = _workflow_version(monkeypatch)
    assert version['workflow_orchestrator']['source-code'] == (
        'https://github.com/odissei-data/'
        'ingestion-workflow-orchestrator/releases/tag/v1.2.3')
