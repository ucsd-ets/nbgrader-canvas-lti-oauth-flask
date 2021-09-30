from . import client

def test_launch_returns_200(client):
    rv = client.get('/launch')
    assert rv.status_code == 200

def test_launch_fails_if_not_logged_in(client):
    rv = client.get('/launch')
    assert b'Authentication error' in rv.get_data()