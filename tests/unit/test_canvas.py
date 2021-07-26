from tests.unit import FakeResponse
from nbgrader_to_canvas.canvas import CanvasWrapper, Token
from nbgrader_to_canvas.models import Users
from canvasapi import Canvas
from unittest.mock import MagicMock
import unittest
import pytest
import time
from nbgrader_to_canvas import db


# TODO: reconfigure user fixture to cover test_get_canvas
@pytest.fixture(autouse = True)
def user():
    old_user = Users.query.filter_by(user_id=114217).first()
    if old_user:
        db.session.delete(old_user)
        db.session.commit()
    user = Users(114217,'13171~EbhqmjsNUmp8M1zLZsMouZtGoZKQTg9KQsUNEIKexBXQRXf13MSFolcWC9VrH0mN',10,'')
    db.session.add(user)
    db.session.commit()
    yield user
    db.session.delete(user)
    db.session.commit()

def test_get_canvas(user):
    canvas_wrapper = CanvasWrapper('https://test.ucsd.instructure.com', {'canvas_user_id': '114217'})
    canvas = canvas_wrapper.get_canvas()
    assert isinstance(canvas,Canvas)


class TestToken(unittest.TestCase):

    @pytest.fixture(autouse = True)
    def user(self):
        old_user = Users.query.filter_by(user_id=114217).first()
        if old_user:
            db.session.delete(old_user)
            db.session.commit()
        self._user = Users(114217,'13171~EbhqmjsNUmp8M1zLZsMouZtGoZKQTg9KQsUNEIKexBXQRXf13MSFolcWC9VrH0mN',10,'')
        db.session.add(self._user)
        db.session.commit()
        yield self._user
        db.session.delete(self._user)
        db.session.commit()

    #setups a 'valid' token for test use
    @pytest.fixture(autouse = True)
    def token(self, user):
        self._token= Token({'api_key':'1234', 
            'canvas_user_id':'114217'}, 114217)

    def test_check_returns_true_if_valid(self):
        expires_in = int(time.time())+61
        self._user.expires_in=expires_in
        self._token._get_WWW_Auth_response = MagicMock(return_value=FakeResponse({'Empty':'string'},200))
        assert self._token.check()

    def test_check_returns_false_if_token_expired(self):
        expires_in = int(time.time())-30
        self._user.expires_in=expires_in
        assert not self._token.check()
        
    def test_check_returns_false_if_missing_api_key(self):
        expires_in = int(time.time())+61
        self._user.expires_in=expires_in
        self._token = Token({'missing_key':'key', 
            'canvas_user_id':'114217'}, 114217)
        assert not self._token.check()

    def test_check_returns_false_if_WWW_Authenticate_present(self):
        expires_in = int(time.time())+61
        self._user.expires_in=expires_in
        self._token._get_WWW_Auth_response = MagicMock(return_value=FakeResponse({'WWW-Authenticate':'string'},200))
        assert not self._token.check()

    def test_unexpired_returns_false_if_expired(self):
        expires_in = int(time.time())-30
        self._user.expires_in=expires_in
        assert not self._token._unexpired()

    def test_unexpired_returns_true_if_not_expired(self):
        expires_in = int(time.time())+61
        self._user.expires_in=expires_in
        assert self._token._unexpired()
    
    def test_contains_api_key_returns_false_if_no_api_key_exists(self):
        self._token = Token({'missing_api_key':'string'}, 114217)
        assert not self._token._contains_api_key()

    def test_contains_api_key_returns_true_if_api_key_exists(self):
        assert self._token._contains_api_key()
    
    def test_valid_WWW_Authenticate_returns_false_if_in_header(self):
        self._token._get_WWW_Auth_response = MagicMock(return_value=FakeResponse({'WWW-Authenticate':'string'},200))
        assert not self._token._valid_WWW_Authenticate()
    
    def test_valid_WWW_Authenticate_returns_true_if_not_in_header(self):
        self._token._get_WWW_Auth_response = MagicMock(return_value=FakeResponse({'Empty':'string'},200))
        assert self._token._valid_WWW_Authenticate()

    def test_update_db_expiration_returns_false_if_db_is_not_updated(self):
        self._token._get_db_expiration = MagicMock(return_value = 10)
        
        assert not self._token._update_db_expiration(13,{'mock session':'string'})
    
    def test_update_db_expiration_returns_true_if_db_is_updated(self):
        assert self._token._update_db_expiration(13,{'mock session':'string'})
    
    def test_refresh_returns_false_if_bad_refresh_key(self):
        self._user.refresh_key='bad_key'
        assert not self._token.refresh()
    
    def test_refresh_returns_true_if_refresh_succeeds(self):
        assert self._token.refresh()