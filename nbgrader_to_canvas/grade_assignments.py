from flask import Blueprint, Response, render_template

from . import app
from .utils import return_error


grade_assignments_blueprint = Blueprint('grade_assignments', __name__)

# grade assignments
@grade_assignments_blueprint.route("/grade_assignments", methods=['GET'], strict_slashes=False)
def grade_assignments():
    """
    Returns the lti.grading_list file for the app.
    grading_list can be built at https://www.eduappcenter.com/
    """
    try:
        return Response(
            render_template('assignments.htm.j2')
        )
    except Exception as e:
        app.logger.error(e)
        import os
        app.logger.error(os.getcwd())
        app.logger.error("No assignemnts file.")
        msg = (
            'No assignments file. Please refresh and try again. '
            'If this error persists, please contact support.'
        )
        return return_error(msg)
