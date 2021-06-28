from nbgrader_to_canvas import canvas
from nbgrader_to_canvas.canvas import CanvasWrapper
from flask import session, redirect, url_for, request, Blueprint
from pylti.flask import lti
from functools import wraps
import time
import requests

from .utils import redirect_to_auth, error, check_valid_user
from . import settings
from .models import AssignmentMatch, Users
from . import app, db

launch_blueprint = Blueprint('launch', __name__)

# only clicked the first time we go to LTI from canvas
# key could expire on later visits
@launch_blueprint.route('/launch', methods=['POST', 'GET'], strict_slashes=False)
@lti(error=error, request='initial', role='staff', app=app)
@check_valid_user
def launch(lti=lti):

    # Try to grab the user
    user = Users.query.filter_by(user_id=int(session['canvas_user_id'])).first()
    app.logger.info("{}".format(user))
    # Found a user
    if not user:
        # User not in database, go go OAuth!!
        app.logger.info(
            "Person doesn't have an entry in db, redirecting to oauth: {0}".format(session)
        )
        return redirect_to_auth()

    app.logger.info("Token: {}".format(user.refresh_key))
    canvas_wrapper = CanvasWrapper()

    if canvas_wrapper.update_token():
        app.logger.debug("redirecting to grade_overview")
        return redirect(url_for('grade_overview.grade_overview'))
    else:
        # Refresh didn't work. Reauthenticate.
        app.logger.info('Reauthenticating:\nSession: {}'.format(session))
        return redirect_to_auth()
