from canvasapi import Canvas
from flask import session

import requests
import json
import time

from . import settings
from . import db, app

from .models import Users


class Token:

    def __init__(self, flask_session, user):
        self._flask_session = flask_session
        self._user = user
        self.token_refresh_threshold = 60

    #Is the token valid
    def check(self):
        if self._unexpired() and self._contains_api_key() and self._valid_WWW_Authenticate():
            return True
        else:
            return False

    # If token expires within threshold return false
    def _unexpired(self):
        expiration_date = self._user.expires_in
        token_ttl = expiration_date - int(time.time())

        if token_ttl < self.token_refresh_threshold:
            app.logger.debug('Expired Token')
            return False
        else:
            return True
     
    def _contains_api_key(self):
        if('api_key' in self._flask_session):
            return True
        else:
            app.logger.debug('Invalid API key')
            return False

    # Only called after _unexpired and _contains_api_key. May error otherwise
    def _valid_WWW_Authenticate(self):
        r = self._get_WWW_Auth_response()
        if 'WWW-Authenticate' not in r.headers and r.status_code == 200:
            return True
        else:
            app.logger.debug('WWW-Authenticate present')
            return False

    #Only called after _unexpired and _contains_api_key. May error otherwise
    def _get_WWW_Auth_response(self):
        auth_header = {'Authorization': 'Bearer ' + self._flask_session['api_key']}
        return requests.get(
            '{}courses/{}/users/{}'.format(settings.API_URL, self._flask_session['course_id'], self._flask_session['canvas_user_id']),
            headers = auth_header
        )
        
    # Combine old refresh function with refresh_access_token

    def refresh(self):
        """
        Use user's refresh token to get a new access token.

        :rtype: bool
        :returns: True if refresh succeeds. False if json response is invalid, 
            or db does not get updated.
        """
        
        payload = {
                'grant_type': 'refresh_token',
                'client_id': settings.oauth2_id,
                'redirect_uri': settings.oauth2_uri,
                'client_secret': settings.oauth2_key,
                'refresh_token': self._user.refresh_key
            }
        response = requests.post(
            settings.BASE_URL + 'login/oauth2/token',
            data=payload
        )

        try:
            api_key = response.json()['access_token']
            app.logger.info(
                'New access token created\n User: {0}'.format(self._user.user_id)
            )

            current_time = int(time.time())
            new_expiration_date = current_time + response.json()['expires_in']
        except Exception as ex:
            app.logger.warning((
                'Access token or expires_in not in json. Bad api key or refresh token.\n'
                'URL: {}\n'
                'Status Code: {}\n'
                'Payload: {}\n'
                'Session: {}\n'
                'Exception: {}'
            ).format(response.url, response.status_code, payload, self._flask_session, ex))
            return False         

        # Update expiration date in db
        if not self._update_db_expiration(new_expiration_date):
            return False

        self._flask_session['api_key'] = api_key
        self._flask_session['expires_in'] = new_expiration_date
        return True

    def _update_db_expiration(self, new_expiration_date, flask_session = session):
        self._user.expires_in = new_expiration_date
        db.session.commit()

        # Confirm that expiration date has been updated
        db_expiration = self._get_db_expiration()
        if db_expiration != new_expiration_date:
            readable_expires_in = time.strftime(
                '%a, %d %b %Y %H:%M:%S',
                time.localtime(db_expiration)
            )
            readable_new_expiration = time.strftime(
                '%a, %d %b %Y %H:%M:%S',
                time.localtime(new_expiration_date)
            )
            app.logger.error((
                'Error in updating user\'s expiration time in the db:\n'
                'session: {}\n'
                'DB expires_in: {}\n'
                'new_expiration_date: {}'
            ).format(flask_session, readable_expires_in, readable_new_expiration))
            return False
        return True

    # This doesn't really need to exist. It is just used to allow mock testing
    def _get_db_expiration(self):
        user = Users.query.filter_by(user_id=int(self._user.user_id)).first()
        return user.expires_in
        
# Wrapper for getting a canvas object and maintaining a fresh token
class CanvasWrapper:

    def __init__(self, api_URL = settings.API_URL, flask_session = session):
        self._api_URL = api_URL
        self._flask_session = flask_session
    
    def get_canvas(self):
        if not self.update_token():
            pass
        return Canvas(self._api_URL, self._flask_session['api_key'])

    # Checks if token up to date. If not, try to refresh it. If refresh fails, then return False. Otherwise return True
    def update_token(self):
        token = self.get_token()
        if not token.check():
            app.logger.debug("Refreshing token")
            token.refresh()
            return False
        return True
    
    def get_token(self):
        user = Users.query.filter_by(user_id=int(self._flask_session['canvas_user_id'])).first()
        return Token(self._flask_session, user)