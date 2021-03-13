from flask import Blueprint, render_template, session, request, url_for, redirect
from pylti.flask import lti

from .utils import get_canvas, error
from . import app
from . import settings


index_blueprint = Blueprint('index', __name__)

# Web Views / Routes
@index_blueprint.route('/index', methods=['GET', 'POST'])
@lti(error=error, request='session', role='staff', app=app)
def index(course_id=None, user_id=None, lti=lti):

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

    session['course_id'] = args['course_id']
    session['user_id'] = args['user_id']
    msg = "hi! Course ID is {}, User ID is {}.".format(session['course_id'], session['user_id'])


    # get canvas assignments
    canvas = get_canvas()

    if canvas is None:
        courses = None
    else:
        courses = canvas.get_courses()

    course_id = session['course_id']
    course = canvas.get_course(course_id)

    if request.method == 'POST':
        # upload grades blueprint is scoped to upload_grades
        # preserve POST method on redirect with 307
        return redirect(url_for('upload_grades.upload_grades'),code=307)

    
    return render_template('index.htm.j2', course_id=session['course_id'], BASE_URL=settings.BASE_URL)
