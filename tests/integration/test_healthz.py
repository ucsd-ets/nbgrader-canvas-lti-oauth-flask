from . import client

def test_healthz_returns_status_code_200(client):
    rv = client.get('/healthz')
    rv.status_code == 200 

def test_healthz_is_json(client):
    rv = client.get('/healthz')

    assert rv.content_type == 'application/json'
    assert 'uptime' in rv.json.keys()
    assert 'message' in rv.json.keys()
