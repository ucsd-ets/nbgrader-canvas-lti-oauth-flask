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
    from canvasapi.assignment import (
        Assignment,
        AssignmentGroup,
        AssignmentOverride,
        AssignmentExtension,
    )
    from canvasapi.progress import Progress
    from canvasapi.course import Course

    # Cool, we got through
    args = request.args.to_dict()

    #session['course_id'] = args['course_id']
    course_id = session['course_id']

    # initialize a new canvasapi Canvas object
    canvas = get_canvas()

    # to do error handling
    #if canvas is None:
    #    courses = None
    #else:
    #    courses = canvas.get_courses()
    course = canvas.get_course(course_id)
    NBGRADER_ASSIGN1_ID = 277845 # canvas "nbgrader assign 1"
    TESTACCT3_USER_ID = 115753
    
    assignment = course.get_assignment(NBGRADER_ASSIGN1_ID)

    # ASK about assignment submission type (external tool)

    # TODO get assignments from canvas first
    # if there is an nbgrader assignment id that is not in canvas,
    # what do we use as id?
    progress = assignment.submissions_bulk_update(
            grade_data={TESTACCT3_USER_ID: {"posted_grade": 97}}
        )

    progress = progress.query()
    #self.assertTrue(progress.context_type == "Course")
    
    return render_template('upload_grades.htm.j2', progress=progress, BASE_URL=settings.BASE_URL)
