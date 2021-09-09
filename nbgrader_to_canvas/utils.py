from flask import redirect, render_template, request, session, url_for
from functools import wraps

from datetime import timedelta

from . import app
from . import settings
from . import db
from circuitbreaker import CircuitBreakerMonitor


# Utility Functions
def return_error(msg):
    return render_template('error.htm.j2', msg=msg, BASE_URL=settings.BASE_URL)


def error(exception=None):
    app.logger.error("PyLTI test3 error: {}".format(exception))
    return return_error('Authentication error, please refresh and try again. If this error persists, please contact support.')


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

def open_circuit():
    '''Fallback function for flask requests.'''
    return redirect(url_for('open'))

def redirect_open_circuit():
    '''Fallback function for ajax requests.'''
    app.logger.debug("Fallback function called")
    return "open", 303
    
@app.route('/open', methods=['POST','GET'])
def open():
    '''Called when circuit breaker is open.'''
    errors = "" 
    for circuit in CircuitBreakerMonitor.get_open():
        errors += "<br>" + str(circuit.last_failure)
    return return_error(
        "The following internal error(s) have occured:" + errors
    ), 500



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
            app.logger.debug(roles)

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

            if "TeachingAssistant" in roles:
                session['teaching assistant'] = True
            elif 'teaching assistant' in session:
                # remove old instructor key from the session
                session.pop('teaching assistant', None)

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

        if 'instructor' not in session and 'admin' not in session and 'teaching assistant' not in session:
            app.logger.warning("Not enrolled as Teacher, TA,  or an Admin. Not allowed.")
            return return_error('''You are not enrolled in this course as a Teacher, TA, or Designer.
            Please refresh and try again. If this error persists, please contact support.''')

        return f(*args, **kwargs)
    return decorated_function

@app.teardown_request
def handle_bad_request(e):
    if e:
        app.logger.error("Error during db transaction.")
        db.session.rollback()
    db.session.remove()
    
    