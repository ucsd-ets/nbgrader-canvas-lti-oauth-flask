from nbgrader_to_canvas.canvas import CanvasWrapper
from flask import session, redirect, url_for, Blueprint
from pylti.flask import lti

from .utils import redirect_to_auth, error, check_valid_user, return_error
from .models import Users
from . import app

launch_blueprint = Blueprint('launch', __name__)

# only clicked the first time we go to LTI from canvas
# key could expire on later visits
@launch_blueprint.route('/launch', methods=['POST', 'GET'], strict_slashes=False)
@lti(error=error, request='initial', role='staff', app=app)
@check_valid_user
def launch(lti=lti):

    user = Users.query.filter_by(user_id=int(session['canvas_user_id'])).first()
    if not user:
        # User not in database, go go OAuth!!
        return redirect_to_auth()

    canvas_wrapper = CanvasWrapper()
    session['api_key'] = user.api_key
    if canvas_wrapper.update_token():
        return redirect(url_for('grade_overview.grade_overview'))
    else:
        # Refresh didn't work. Reauthenticate.
        return redirect_to_auth()
