from flask import Blueprint, Response, render_template

from . import app
from .utils import return_error

from .upload_grades import upload_grades

grade_overview_blueprint = Blueprint('grade_overview', __name__)

# grade_overview
@grade_overview_blueprint.route("/grade_overview", methods=['GET'], strict_slashes=False)
def grade_overview():
    """
    Returns the lti.grade_overview file for the app.
    grade_overview can be built at https://www.eduappcenter.com/
    """
    try:
        nbgrader = upload_grades()
        return Response(
            render_template('overview.htm.j2', nbgrader=nbgrader)
        )
    except Exception as e:
        app.logger.error(e)
        import os
        app.logger.error(os.getcwd())
        app.logger.error("No overview file.")
        msg = (
            'No grade_overview file. Please refresh and try again. '
            'If this error persists, please contact support.'
        )
        return return_error(msg)