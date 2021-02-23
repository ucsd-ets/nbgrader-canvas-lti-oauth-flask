from flask import Blueprint, request, session, redirect, url_for
from pylti.flask import lti
import requests
import time

from . import app, db
from . import settings
from .utils import return_error, error, check_valid_user
from .models import Users


oauth_login_blueprint = Blueprint('oauthlogin', __name__)

@oauth_login_blueprint.route('/oauthlogin', methods=['POST', 'GET'])
@lti(error=error, role='staff', app=app)
@check_valid_user
def oauth_login(lti=lti):
    code = request.args.get('code')

    if not code:
        error = request.args.get('error', 'None given')
        error_description = request.args.get('error_description', 'None given')
        app.logger.error('''OAUTH did not return a code we could use to sign in. Canvas says:
        Error: {0}
        Error description: {1}'''.format(error, error_description))

        msg = '''Authentication error,
            please refresh and try again. If this error persists,
            please contact support.'''
        return return_error(msg)

    payload = {
        'grant_type': 'authorization_code',
        'client_id': settings.oauth2_id,
        'redirect_uri': settings.oauth2_uri,
        'client_secret': settings.oauth2_key,
        'code': code
    }
    r = requests.post(settings.BASE_URL+'login/oauth2/token', data=payload)

    if r.status_code == 500:
        # Canceled oauth or server error
        app.logger.error(
            '''Status code 500 from oauth, authentication error\n
            User ID: None Course: None \n {0} \n Request headers: {1} \n Session: {2}'''.format(
                r.url, r.headers, session
            )
        )

        msg = '''Authentication error,
            please refresh and try again. If this error persists,
            please contact support.'''
        return return_error(msg)

    elif r.status_code == 422:
        # https://github.com/instructure/canvas-lms/issues/1343
        app.logger.error(
            "Status code 422 from oauth, are your oauth scopes valid?"
        )

        msg = '''Authentication error,
            please refresh and try again. If this error persists,
            please contact support.'''
        return return_error(msg)


    if 'access_token' in r.json():
        session['api_key'] = r.json()['access_token']

        refresh_token = r.json()['refresh_token']

        if 'expires_in' in r.json():
            # expires in seconds
            # add the seconds to current time for expiration time
            current_time = int(time.time())
            expires_in = current_time + r.json()['expires_in']
            session['expires_in'] = expires_in

            # check if user is in the db
            user = Users.query.filter_by(user_id=int(session['canvas_user_id'])).first()
            if user is not None:
                # update the current user's expiration time in db
                user.refresh_key = refresh_token
                user.expires_in = session['expires_in']
                db.session.add(user)
                db.session.commit()

                # check that the expires_in time got updated
                check_expiration = Users.query.filter_by(user_id=int(session['canvas_user_id']))

                # compare what was saved to the old session
                # if it didn't update, error
                if check_expiration.expires_in == long(session['expires_in']):
                    course_id = session['course_id']
                    user_id = session['canvas_user_id']
                    print (course_id)
                    print (user_id)
                    return redirect(url_for('index.index', course_id=course_id, user_id=user_id))
                else:
                    app.logger.error(
                        '''Error in updating user's expiration time
                        in the db:\n {0}'''.format(session))
                    return return_error('''Authentication error,
                            please refresh and try again. If this error persists,
                            please contact support.''')
            else:
                # add new user to db
                new_user = Users(
                    session['canvas_user_id'],
                    refresh_token,
                    session['expires_in']
                )
                db.session.add(new_user)
                db.session.commit()

                # check that the user got added
                check_user = Users.query.filter_by(user_id=int(session['canvas_user_id'])).first()

                if check_user is None:
                    # Error in adding user to the DB
                    app.logger.error(
                        "Error in adding user to db: \n {0}".format(session)
                    )
                    return return_error('''Authentication error,
                        please refresh and try again. If this error persists,
                        please contact support.''')
                else:
                    course_id = session['course_id']
                    user_id = session['canvas_user_id']
                    return redirect(url_for('index.index', course_id=course_id, user_id=user_id))

            # got beyond if/else
            # error in adding or updating db

            app.logger.error(
                "Error in adding or updating user to db: \n {0} ".format(session)
            )
            return return_error('''Authentication error,
                please refresh and try again. If this error persists,
                please contact support.''')

    app.logger.warning(
        "Some other error\n {0} \n {1} \n Request headers: {2} \n {3}".format(
            session, r.url, r.headers, r.json()
        )
    )
    msg = '''Authentication error,
        please refresh and try again. If this error persists,
        please contact support.'''
    return return_error(msg)
