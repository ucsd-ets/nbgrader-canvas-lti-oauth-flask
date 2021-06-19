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
            return False
        else:
            return True
     
    def _contains_api_key(self):
        if('api_key' in self._flask_session):
            return True
        else:
            return False

    def _valid_WWW_Authenticate(self):
        
        #TODO: Testing requests from a page that doesn't exist. Fix
        return True
        auth_header = {'Authorization': 'Bearer ' + self._flask_session['api_key']}
        r = requests.get(
            '{}users/{}'.format(settings.API_URL, self._flask_session['canvas_user_id']),
            headers = auth_header
        )
        print('WWW-Authenticate' not in r.headers)
        print(r.status_code)
        print(r.url)
        if 'WWW-Authenticate' not in r.headers and r.status_code == 200:
            return True
        else:
            return False
        
    # Combine old refresh function with refresh_access_token

    def refresh(self):
        """
        Use user's refresh token to get a new access token.

        :rtype: bool
        :returns: True if refresh succeeds. False if json response is invalid, 
            or db does not get updated.
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

    def _update_db_expiration(self, new_expiration_date):
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
        
#TODO: consider renaming to something more descriptive
class NbgraderCanvas:

    def __init__(self, api_URL, flask_session = session):
        self._api_URL = api_URL
        self._flask_session = flask_session
    
    def get_canvas(self):
        self.update_token()
        return Canvas(self._api_URL, self._flask_session['api_key'])

    # Checks if token up to date. If not, try to refresh it. If refresh fails, then return False. Otherwise return True
    def update_token(self):
        user = Users.query.filter_by(user_id=int(self._flask_session['canvas_user_id'])).first()
        token = Token(self._flask_session, user)
        if not token.check():
            return token.refresh()
        return True