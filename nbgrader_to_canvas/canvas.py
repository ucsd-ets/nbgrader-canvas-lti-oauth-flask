from canvasapi import Canvas
from flask import session

import requests
import json
import time

from . import settings
from . import db

from .models import Users


class Token:

    def __init__(self, flask_session, user):
        self._flask_session = flask_session
        self._user = user
        self.token_refresh_threshold = 60

    def check(self):
        if self.unexpired() and self.valid_api_key() and self.valid_WWW_Authenticate():
            return True
        else:
            return False

        # expiration_date = self._user.expires_in
        # token_ttl = expiration_date - int(time.time())

        # if token_ttl < self.token_refresh_threshold:
        #     return False
        # elif 'api_key' not in self._flask_session:
        #     return False
        #     # TODO: Figure out what to do here
        #     # Need to know which false is being returned
        # return True



    #If token expires within threshold return false
    def unexpired(self):
        expiration_date = self._user.expires_in
        token_ttl = expiration_date - int(time.time())

        if token_ttl < self.token_refresh_threshold:
            return False
        else:
            return True
     
    def valid_api_key(self):
        if('api_key' in self._flask_session):
            return True
        else:
            return False

    def valid_WWW_Authenticate(self, override=True):
        #TODO: figure out how to spoof this properly instead of just overriding the return to test
        auth_header = {'Authorization': 'Bearer ' + self._flask_session['api_key']}
        r = requests.get(
            '{}users/{}'.format(settings.API_URL, self._flask_session['canvas_user_id']),
            headers=auth_header
        )

        print(r.headers)
        print(r.status_code)
        if override or 'WWW-Authenticate' not in r.headers and r.status_code == 200:
            return True
        else:
            return False
        
    # Combine old refresh function with refresh_access_token

    def refresh(self):
        """
        Use user's refresh token to get a new access token.

        :rtype: bool
        :returns: True if refresh succeeds. False if json response is invalid, 
            or db does not get updatedDictionary with keys 'access_token' and 'expiration_date'.
        """
        # TODO: Potentially refactor the response and json segment to make this function more testable
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

        if 'access_token' not in response.json() or 'expires_in' not in response.json():
            app.logger.warning((
                'Access token or expires_in not in json. Bad api key or refresh token.\n'
                'URL: {}\n'
                'Status Code: {}\n'
                'Payload: {}\n'
                'Session: {}'
            ).format(response.url, response.status_code, payload, self._flask_session))
            return False            

        api_key = response.json()['access_token']
        app.logger.info(
            'New access token created\n User: {0}'.format(self._user.user_id)
        )

        current_time = int(time.time())
        new_expiration_date = current_time + response.json()['expires_in']

        # Update expiration date in db
        if not self.update_db_expiration(new_expiration_date):
            return False

        self._flask_session['api_key'] = api_key
        self._flask_session['expires_in'] = new_expiration_date
        return True

    def update_db_expiration(self, new_expiration_date):
        self._user.expires_in = new_expiration_date
        db.session.commit()

        # Confirm that expiration date has been updated
        updated_user = Users.query.filter_by(user_id=int(self._user.user_id)).first()
        if updated_user.expires_in != new_expiration_date:
            readable_expires_in = time.strftime(
                '%a, %d %b %Y %H:%M:%S',
                time.localtime(updated_user.expires_in)
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
            ).format(session, readable_expires_in, readable_new_expiration))
            return False
        return True
        
#TODO: rename to avoid confusion
class NbgraderCanvas:

    def __init__(self, api_URL, flask_session = session):
        self._api_URL = api_URL
        self._flask_session = flask_session
    
    def get_canvas(self):
        # update_token()
        return Canvas(self._api_URL, self._flask_session['api_key'])

    # Checks if token up to date. If not, try to refresh it. If refresh fails, then return False. Otherwise return True
    def update_token(self, flask_session=session):
        user = Users.query.filter_by(user_id=int(flask_session['canvas_user_id'])).first()
        token = Token(flask_session, user)
        if not token.check():
            return token.refresh()
        return True