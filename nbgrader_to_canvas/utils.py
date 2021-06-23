from flask import redirect, render_template, url_for, request, session
from functools import wraps

import requests
import time

from datetime import timedelta
from canvasapi import Canvas

from . import app
from . import settings
from . import db
from .models import Users


# Utility Functions
def return_error(msg):
    return render_template('error.htm.j2', msg=msg)


def error(exception=None):
    app.logger.error("PyLTI error: {}".format(exception))
    return return_error('''Authentication error,
        please refresh and try again. If this error persists,
        please contact support.''')


def redirect_to_auth():
    """Redirects the user to the Canvas OAUTH flow

    This function uses BASE_URL and the oauth settings from settings.py to redirect the
    user to the appropriate place in their Canvas installation for authentication.
    """
    return redirect(
        "{}login/oauth2/auth?client_id={}&response_type=code&redirect_uri={}&scope={}".format(
            settings.BASE_URL, settings.oauth2_id, settings.oauth2_uri, settings.oauth2_scopes
        )
    )


def check_valid_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        """
        Decorator to check if the user is allowed access to the app.

        If user is allowed, return the decorated function.
        Otherwise, return an error page with corresponding message.
        """
        
        if request.form:
            session.permanent = True
            # 1 hour long session
            app.permanent_session_lifetime = timedelta(minutes=60)
            session['course_id'] = request.form.get('custom_canvas_course_id')
            session['canvas_user_id'] = request.form.get('custom_canvas_user_id')
            roles = request.form['roles']

            if "Administrator" in roles:
                session['admin'] = True
                session['instructor'] = True
            elif 'admin' in session:
                # remove old admin key in the session
                session.pop('admin', None)

            if "Instructor" in roles:
                session['instructor'] = True
            elif 'instructor' in session:
                # remove old instructor key from the session
                session.pop('instructor', None)

        # no session and no request
        if not session:
            if not request.form:
                app.logger.warning("No session and no request. Not allowed.")
                return return_error('No session or request provided.')

        # no canvas_user_id
        if not request.form.get('custom_canvas_user_id') and 'canvas_user_id' not in session:
            app.logger.warning("No canvas user ID. Not allowed.")
            return return_error('No canvas uer ID provided.')

        # no course_id
        if not request.form.get('custom_canvas_course_id') and 'course_id' not in session:
            app.logger.warning("No course ID. Not allowed.")
            return return_error('No course_id provided.')

        # If they are neither instructor or admin, they're not in the right place

        if 'instructor' not in session and 'admin' not in session:
            app.logger.warning("Not enrolled as Teacher or an Admin. Not allowed.")
            return return_error('''You are not enrolled in this course as a Teacher or Designer.
            Please refresh and try again. If this error persists, please contact support.''')

        return f(*args, **kwargs)
    return decorated_function

# def check_token_freshness(user):
#     # Get the expiration date
#     expiration_date = user.expires_in
#     token_refresh_threshold = 60
#     token_ttl = expiration_date - int(time.time())

#     # refresh the key if it will expire within the next minute, just to make sure the key doesn't expire while responding to a request.
#     app.logger.debug("Token expires in {} seconds, refreshing if less than threshold of {}".format(token_ttl, token_refresh_threshold))
#     if token_ttl < token_refresh_threshold or 'api_key' not in session:
#         readable_time = time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime(user.expires_in))

#         app.logger.info((
#             'Expired refresh token or api_key not in session\n'
#             'User: {0}\n'
#             'Expiration date in db: {1}\n'
#             'Readable expires_in: {2}'
#         ).format(user.user_id, user.expires_in, readable_time))

#         refresh = refresh_access_token(user)

#         if refresh['access_token'] and refresh['expiration_date']:
#             # Success! Set the API Key and Expiration Date
#             session['api_key'] = refresh['access_token']
#             session['expires_in'] = refresh['expiration_date']
            
#             return True
#         else:
#             return False
#     else:
        
#         # Have an API key that shouldn't be expired. Test it to be sure.
#         auth_header = {'Authorization': 'Bearer ' + session['api_key']}
#         r = requests.get(
#             '{}users/{}'.format(settings.API_URL, session['canvas_user_id']),
#             headers=auth_header
#         )

#         # check for WWW-Authenticate
#         # https://canvas.instructure.com/doc/api/file.oauth.html
#         if 'WWW-Authenticate' not in r.headers and r.status_code == 200:
            
#             return True
#         else:
#             # Key is bad. First try to get a new one using refresh
#             new_token = refresh_access_token(user)['access_token']

#             if new_token:
#                 session['api_key'] = new_token
#                 return True
#             else:
#                 # Refresh didn't work. Reauthenticate.
#                 app.logger.info('Reauthenticating:\nSession: {}'.format(session))
#                 return False

# def refresh_access_token(user):
#     """
#     Use a user's refresh token to get a new access token.

#     :param user: The user to get a new access token for.
#     :type user: :class:`Users`

#     :rtype: dict
#     :returns: Dictionary with keys 'access_token' and 'expiration_date'.
#         Values will be `None` if refresh fails.
#     """
#     refresh_token = user.refresh_key

#     payload = {
#             'grant_type': 'refresh_token',
#             'client_id': settings.oauth2_id,
#             'redirect_uri': settings.oauth2_uri,
#             'client_secret': settings.oauth2_key,
#             'refresh_token': refresh_token
#         }
#     response = requests.post(
#         settings.BASE_URL + 'login/oauth2/token',
#         data=payload
#     )

#     if 'access_token' not in response.json():
#         app.logger.warning((
#             'Access token not in json. Bad api key or refresh token.\n'
#             'URL: {}\n'
#             'Status Code: {}\n'
#             'Payload: {}\n'
#             'Session: {}'
#         ).format(response.url, response.status_code, payload, session))
#         return {
#             'access_token': None,
#             'expiration_date': None
#         }

#     api_key = response.json()['access_token']
#     app.logger.info(
#         'New access token created\n User: {0}'.format(user.user_id)
#     )


#     if 'expires_in' not in response.json():
#         app.logger.warning((
#             'expires_in not in json. Bad api key or refresh token.\n'
#             'URL: {}\n'
#             'Status Code: {}\n'
#             'Payload: {}\n'
#             'Session: {}'
#         ).format(response.url, response.status_code, payload, session))
#         return {
#             'access_token': None,
#             'expiration_date': None
#         }

#     current_time = int(time.time())
#     new_expiration_date = current_time + response.json()['expires_in']

#     # Update expiration date in db
#     user.expires_in = new_expiration_date
#     db.session.commit()

#     # Confirm that expiration date has been updated
#     updated_user = Users.query.filter_by(user_id=int(user.user_id)).first()
#     if updated_user.expires_in != new_expiration_date:
#         readable_expires_in = time.strftime(
#             '%a, %d %b %Y %H:%M:%S',
#             time.localtime(updated_user.expires_in)
#         )
#         readable_new_expiration = time.strftime(
#             '%a, %d %b %Y %H:%M:%S',
#             time.localtime(new_expiration_date)
#         )
#         app.logger.error((
#             'Error in updating user\'s expiration time in the db:\n'
#             'session: {}\n'
#             'DB expires_in: {}\n'
#             'new_expiration_date: {}'
#         ).format(session, readable_expires_in, readable_new_expiration))
#         return {
#             'access_token': None,
#             'expiration_date': None
#         }

#     return {
#         'access_token': api_key,
#         'expiration_date': new_expiration_date
#     }
    
# initialize a new Canvas object
# see https://github.com/ucfopen/canvasapi/issues/238
# /oauthlogin sets session["api_key"] then redirects to /index
# def get_canvas():
#     try:
#         user = Users.query.filter_by(user_id=int(session['canvas_user_id'])).first()

#         if check_token_freshness(user):
#             canvas = Canvas(settings.API_URL, session['api_key'])
#             return canvas
#     except Exception as ex:
#         app.logger.error("An error occurred connecting to Canvas: {}".format(ex))
#         raise
