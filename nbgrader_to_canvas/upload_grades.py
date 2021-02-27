from flask import Blueprint, render_template, session, request
from pylti.flask import lti

from .utils import get_canvas, error
from . import app
from . import settings


upload_grades_blueprint = Blueprint('upload_grades', __name__)

# Web Views / Routes
@upload_grades_blueprint.route('/upload_grades', methods=['GET'])
@lti(error=error, request='session', role='staff', app=app)
def upload_grades(lti=lti):

    import sys
    import os
    import canvasapi
    import pytest
    # Import the Canvas class
    from canvasapi.submission import GroupedSubmission, Submission
    from canvasapi.upload import Uploader
    from canvasapi.assignment import (
        Assignment,
        AssignmentGroup,
        AssignmentOverride,
        AssignmentExtension,
    )
    from canvasapi.group import Group, GroupCategory, GroupMembership

    # Cool, we got through
    args = request.args.to_dict()

    # initialize a new canvasapi Canvas object
    canvas = get_canvas()

    if canvas is None:
        courses = None
    else:
        courses = canvas.get_courses()
    
    return render_template('upload_grades.htm.j2', BASE_URL=settings.BASE_URL)
