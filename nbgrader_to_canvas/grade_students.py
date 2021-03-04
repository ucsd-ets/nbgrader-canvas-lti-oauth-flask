from flask import Blueprint, Response, render_template

from . import app
from .utils import return_error


grade_students_blueprint = Blueprint('grade_students', __name__)

# grade assignments
@grade_students_blueprint.route("/grade_students", methods=['GET'], strict_slashes=False)
def grade_students():
    """
    Returns the lti.grading_list file for the app.
    grading_list can be built at https://www.eduappcenter.com/
    """
    try:
        return Response(
            render_template('students.htm.j2')
        )
    except Exception as e:
        app.logger.error(e)
        import os
        app.logger.error(os.getcwd())
        app.logger.error("No students file.")
        msg = (
            'No students file. Please refresh and try again. '
            'If this error persists, please contact support.'
        )
        return return_error(msg)