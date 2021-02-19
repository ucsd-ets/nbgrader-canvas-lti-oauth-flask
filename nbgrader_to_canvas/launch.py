from flask import session, redirect, url_for, request, Blueprint
from pylti.flask import lti
from functools import wraps
import time
import requests

from .utils import redirect_to_auth, refresh_access_token, error, check_valid_user
from . import settings
from .models import Users
from . import app

launch_blueprint = Blueprint('launch', __name__)

# only clicked the first time we go to LTI from canvas
# key could expire on later visits
@launch_blueprint.route('/launch', methods=['POST', 'GET'], strict_slashes=False)
@lti(error=error, request='initial', role='staff', app=app)
@check_valid_user
def launch(lti=lti):
    
    # Try to grab the user
    user = Users.query.filter_by(user_id=int(session['canvas_user_id'])).first()

    # Found a user
    if not user:
        # User not in database, go go OAuth!!
        app.logger.info(
            "Person doesn't have an entry in db, redirecting to oauth: {0}".format(session)
        )
        return redirect_to_auth()

    # Get the expiration date
    expiration_date = user.expires_in
    
    # If expired or no api_key
    # mf: refresh the key if it will expire within the next minute, just to make sure the key doesn't expire while responding to a request.
    #if int(time.time()) > expiration_date or 'api_key' not in session:
    if int(time.time()) - 60 > expiration_date or 'api_key' not in session:
        readable_time = time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime(user.expires_in))

        app.logger.info((
            'Expired refresh token or api_key not in session\n'
            'User: {0}\n'
            'Expiration date in db: {1}\n'
            'Readable expires_in: {2}'
        ).format(user.user_id, user.expires_in, readable_time))

        refresh = refresh_access_token(user)

        if refresh['access_token'] and refresh['expiration_date']:
            # Success! Set the API Key and Expiration Date
            session['api_key'] = refresh['access_token']
            session['expires_in'] = refresh['expiration_date']
            
            return redirect(url_for(
                'index',
                course_id=session['course_id'],
                user_id=session['canvas_user_id']
            ))
        else:
            # Refresh didn't work. Reauthenticate.
            app.logger.info('Reauthenticating:\nSession: {}'.format(session))
            return redirect_to_auth()
    else:
        
        # Have an API key that shouldn't be expired. Test it to be sure.
        auth_header = {'Authorization': 'Bearer ' + session['api_key']}
        r = requests.get(
            # matthew noted this is broken
#           '{}users/{}/profile'.format(settings.API_URL, session['canvas_user_id']),
            '{}users/{}'.format(settings.API_URL, session['canvas_user_id']),
            headers=auth_header
        )

        # check for WWW-Authenticate
        # https://canvas.instructure.com/doc/api/file.oauth.html
        if 'WWW-Authenticate' not in r.headers and r.status_code == 200:
            
            return redirect(url_for(
                'index',
                course_id=session['course_id'],
                user_id=session['canvas_user_id']
            ))
        else:
            # Key is bad. First try to get a new one using refresh
            new_token = refresh_access_token(user)['access_token']

            if new_token:
                session['api_key'] = new_token
                return redirect(url_for(
                    'index',
                    course_id=session['course_id'],
                    user_id=session['canvas_user_id']
                ))
            else:
                # Refresh didn't work. Reauthenticate.
                app.logger.info('Reauthenticating:\nSession: {}'.format(session))
                return redirect_to_auth()