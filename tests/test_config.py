from configuration import config


def test_public_url(monkeypatch):
    monkeypatch.setattr(config, 'settings', {
        'PUBLIC_URLS': {'http://mapper:8082': 'https://mapper.example.org'}})
    assert config.public_url('http://mapper:8082/mapper') == 'https://mapper.example.org/mapper'
    assert config.public_url('http://mapper:8082') == 'https://mapper.example.org'
    assert config.public_url('http://mapper:80821/mapper') == 'http://mapper:80821/mapper'
    assert config.public_url('http://seaweedfs:9002/healthz') == 'http://seaweedfs:9002/healthz'
