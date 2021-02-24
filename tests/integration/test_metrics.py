from . import client

def test_metrics_returns_200(client):
    rv = client.get('/metrics')
    assert rv.status_code == 200
