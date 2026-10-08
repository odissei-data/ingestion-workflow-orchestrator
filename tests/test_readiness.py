import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import readiness


class Stub(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/users/:me':
            valid = self.headers.get('X-Dataverse-key') == 'valid'
            self.send_response(200 if valid else 401)
        else:
            self.send_response(200 if self.path == '/health' else 503)
        self.end_headers()

    def log_message(self, *args):
        pass


def test_check():
    server = HTTPServer(('127.0.0.1', 0), Stub)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}'
    try:
        assert readiness.check(base + '/health') == 'ok'
        assert readiness.check(base + '/ready') == 'HTTP 503'
        me = base + '/api/users/:me'
        assert readiness.check(me, {'X-Dataverse-key': 'valid'}) == 'ok'
        assert readiness.check(me, {'X-Dataverse-key': 'expired'}) == 'HTTP 401'
    finally:
        server.shutdown()
        server.server_close()
    assert readiness.check(base + '/health') == 'ConnectionError'


def test_paths_keep_the_url_prefix(monkeypatch):
    class Settings(dict):
        __getattr__ = dict.__getitem__

    urls = {name: 'http://service/app/endpoint' for name, _ in readiness.CHECKS}
    urls.update(ODISSEI_URL='http://portal/', ODISSEI_API_KEY='key',
                VERSION_TRACKER_STORE_URL='http://portal/version-tracker/store')
    monkeypatch.setattr(readiness, 'settings', Settings(urls))
    monkeypatch.setattr(readiness, 'check', lambda url, headers=None: 'ok')
    checked = [url for url, _ in readiness.run_checks()]
    assert 'http://portal/version-tracker/ready' in checked
    assert 'http://portal/api/users/:me' in checked
