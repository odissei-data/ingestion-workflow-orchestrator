from unittest.mock import Mock

import pytest
from prefect.logging import disable_run_logger

from configuration import config
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
        'image': 'ghcr.io/odissei-data/dataverse-mapper:v2.1.0'})
    assert record == {
        'name': 'dataverse-mapper',
        'version': 'v2.1.0',
        'docker-image': 'ghcr.io/odissei-data/dataverse-mapper:v2.1.0',
        'endpoint': 'http://mapper:8082/mapper',
    }


def test_openapi_version_has_no_image(monkeypatch):
    record = _record(monkeypatch, {'info': {'version': '0.3.0'}})
    assert record['version'] == '0.3.0'
    assert record['docker-image'] is None


def test_missing_version_fails(monkeypatch):
    with pytest.raises(ValueError):
        _record(monkeypatch, {'status': 'ok'})


def test_endpoints_are_recorded_by_their_public_url(monkeypatch):
    monkeypatch.setattr(config, 'settings', {
        'PUBLIC_URLS': {'http://mapper:8082': 'https://mapper.example.org'}})
    record = _record(monkeypatch, {'status': 'ok', 'version': 'v2.1.0'})
    assert record['endpoint'] == 'https://mapper.example.org/mapper'
