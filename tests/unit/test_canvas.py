from nbgrader_to_canvas.canvas import NbgraderCanvas, Token
from nbgrader_to_canvas.models import Users
from canvasapi import Canvas
from flask import session
import unittest
import time
from nbgrader_to_canvas import db

def test_get_canvas():
    canvas = NbgraderCanvas('123','https://google.com')
    canvas = canvas.get_canvas()
    assert isinstance(canvas,Canvas)


class TestToken(unittest.TestCase):

    #TODO: setup fixture(s) that setup the tests to condense code

    def test_check_returns_false_if_valid(self):
        expires_in = int(time.time())-30
        user = Users(1,'string',expires_in)
        token = Token({'api_key':'string', 'canvas_user_id':'string'},user)
        assert not token.check()

    def test_check_returns_true_if_not_valid(self):
        expires_in = int(time.time())+61
        user = Users(1,'string',expires_in)
        token = Token({'api_key':'string', 'canvas_user_id':'string'}, user)
        assert token.check()

    def test_unexpired_returns_false_if_expired(self):
        expires_in = int(time.time())-30
        user = Users(1,'string',expires_in)
        token = Token({'api_key':'string'},user)
        assert not token.unexpired()

    def test_unexpired_returns_true_if_not_expired(self):
        expires_in = int(time.time())+61
        user = Users(1,'string',expires_in)
        token = Token({'api_key':'string'}, user)
        assert token.unexpired()
    
    def test_valid_api_key_returns_false_if_no_api_key_exists(self):
        user = Users(1,'string',10)
        token = Token({'missing_api_key':'string'}, user)
        assert not token.valid_api_key()

    def test_valid_api_key_returns_true_if_api_key_exists(self):
        user = Users(1,'string',10)
        token = Token({'api_key':'string'}, user)
        assert token.valid_api_key()
    
    def test_valid_WWW_Authenticate_returns_false_if_in_header(self):
        user = Users(1,'string',10)
        token = Token({'api_key':'string', 'canvas_user_id':'string'}, user)
        assert not token.valid_WWW_Authenticate(False)
    
    def test_valid_WWW_Authenticate_returns_true_if_not_in_header(self):
        user = Users(1,'string',10)
        token = Token({'api_key':'string', 'canvas_user_id':'string'}, user)
        assert token.valid_WWW_Authenticate()

    
    def test_valid_json_response_returns_false_if_json_missing_access_token(self):
        user = Users(1,'string',10)
        token = Token({'api_key':'string', 'canvas_user_id':'string'}, user)
        json = {'expires_in':61}
        assert not token.valid_json_response(json)
    
    def test_valid_json_response_returns_false_if_json_missing_expiration(self):
        user = Users(1,'string',10)
        token = Token({'api_key':'string', 'canvas_user_id':'string'}, user)
        json = {'access_token':'string'}
        assert not token.valid_json_response(json)

    def test_valid_json_response_true_if_json_contains_access_token_and_expiration(self):
        user = Users(1,'string',10)
        token = Token({'api_key':'string', 'canvas_user_id':'string'}, user)
        json = {'access_token':'string', 'expires_in':61}
        assert token.valid_json_response(json)

    def test_update_db_expiration_returns_false_if_db_is_not_updated(self):
        #TODO: make a test that causes this method to return false. What would cause the commit to fail
        assert False
        old_user = Users.query.filter_by(user_id=1).first()
        if old_user:
            db.session.delete(old_user)
            db.session.commit()
        user = Users(1,'string',10)
        token = Token({'api_key':'string', 'canvas_user_id':'string'}, user)
        db.session.add(user)
        db.session.commit()
        assert token.update_db_expiration(13)
        db.session.delete(user)
        db.session.commit()
    
    def test_update_db_expiration_returns_true_if_db_is_updated(self):
        old_user = Users.query.filter_by(user_id=1).first()
        if old_user:
            db.session.delete(old_user)
            db.session.commit()
        user = Users(1,'string',10)
        token = Token({'api_key':'string', 'canvas_user_id':'string'}, user)
        db.session.add(user)
        db.session.commit()
        assert token.update_db_expiration(13)
        db.session.delete(user)
        db.session.commit()
    

    
    # def test_refresh_returns_false_if_refresh_fails(self):
    #     user = Users(1, 'string', 1)
    #     token = Token({'api_key':'string'},user)
    #     assert token.refresh()
    
    def test_refresh_returns_true_if_refresh_succeeds(self):
        user = Users(1, 'string', 1)
        token = Token({'api_key':'string'},user)
        assert token.refresh()