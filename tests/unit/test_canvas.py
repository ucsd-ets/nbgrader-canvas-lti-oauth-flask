from nbgrader_to_canvas.canvas import NbgraderCanvas, Token
from nbgrader_to_canvas.models import Users
from canvasapi import Canvas
from flask import session
import unittest
import pytest
import time
from nbgrader_to_canvas import db


def test_get_canvas():
    canvas = NbgraderCanvas('123','https://google.com')
    canvas = canvas.get_canvas()
    assert isinstance(canvas,Canvas)


class TestToken(unittest.TestCase):

    @pytest.fixture(autouse = True)
    def user(self):
        self._user = Users(1,'13171~qKHvThhYQrIr0HfTicEEfmBD1DeLG7YM7FZD4RMtf5iFfoyr1eFPKy7lR8kWxJWT',10)
        db.session.add(self._user)
        db.session.commit()
        yield self._user
        db.session.delete(self._user)
        db.session.commit()

    #setups a 'valid' token for test use
    @pytest.fixture(autouse = True)
    def token(self, user):
        self._token= Token({'api_key':'key', 
            'canvas_user_id':'139469'}, self._user)

    def test_check_returns_true_if_valid(self):
        expires_in = int(time.time())+61
        self._user.expires_in=expires_in
        assert self._token.check()

    def test_check_returns_false_if_not_valid(self):
        expires_in = int(time.time())-30
        self._user.expires_in=expires_in
        assert not self._token.check()

    def test_unexpired_returns_false_if_expired(self):
        expires_in = int(time.time())-30
        self._user.expires_in=expires_in
        assert not self._token.unexpired()

    def test_unexpired_returns_true_if_not_expired(self):
        expires_in = int(time.time())+61
        self._user.expires_in=expires_in
        assert self._token.unexpired()
    
    def test_valid_api_key_returns_false_if_no_api_key_exists(self):
        self._token = Token({'missing_api_key':'string'}, self._user)
        assert not self._token.valid_api_key()

    def test_valid_api_key_returns_true_if_api_key_exists(self):
        assert self._token.valid_api_key()
    
    def test_valid_WWW_Authenticate_returns_false_if_in_header(self):
        assert not self._token.valid_WWW_Authenticate(False)
    
    def test_valid_WWW_Authenticate_returns_true_if_not_in_header(self):
        assert self._token.valid_WWW_Authenticate()

    # def test_update_db_expiration_returns_false_if_db_is_not_updated(self):
    #     #TODO: make a test that causes this method to return false. What would cause the commit to fail
    #     assert False
        
    #     assert self._token.update_db_expiration(13)
    
    def test_update_db_expiration_returns_true_if_db_is_updated(self):
        assert self._token.update_db_expiration(13)
    
    # def test_refresh_returns_false_if_refresh_fails(self):
    #     assert not self._token.refresh()
    
    def test_refresh_returns_true_if_refresh_succeeds(self):
        assert self._token.refresh()