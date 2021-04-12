from flask import Blueprint, Response, render_template, session, request
from pylti.flask import lti

from . import app
from .utils import get_canvas, return_error

from nbgrader.api import Gradebook

grade_overview_blueprint = Blueprint('grade_overview', __name__)

# grade_overview
@grade_overview_blueprint.route("/grade_overview", methods=['GET'], strict_slashes=False)
def grade_overview():
    """
    Returns the overview file for the app.
    grade_overview can be viewed at overview.htm.j2
    """
    try:
        nb_assignments = get_nbgrader_assignments()
        canvas_assignments = get_canvas_assignments()
        return Response(
            render_template('overview.htm.j2', nb_assign=nb_assignments, cv_assign=canvas_assignments)
        )
    except Exception as e:
        app.logger.error(e)
        import os
        app.logger.error(os.getcwd())
        app.logger.error("No overview file.")
        msg = (
            'Issues with the grade_overview file. Please refresh and try again. '
            'If this error persists, please contact support.'
        )
        return return_error(msg)


def get_nbgrader_assignments(course="TEST_NBGRADER"):
    """
    Get the nbgrader_assignments from the course gradebook
    """
    # get the gradebook and return the assignments
    with Gradebook("sqlite:////mnt/nbgrader/"+course+"/grader/gradebook.db") as gb:
        return gb.assignments


@lti(request='session', role='staff')
def get_canvas_assignments(lti=lti):
    """
    Get the assignments for the Canvas course
    """

    # get the course id
    course_id = session['course_id']

    # initialize a new canvasapi Canvas object
    canvas = get_canvas()

    # get canvas assignment groups from course
    course = canvas.get_course(course_id)
    assignment_groups = course.get_assignment_groups()

    # find the "Assignments" group
    for ag in assignment_groups:
        if (ag.name == "Assignments"):
            group = course.get_assignment_group(ag.id)
            break

    assignments = course.get_assignments_for_group(group)

    # split the name and id for each course assignment
    canvas_assignments = {}
    canvas_assignments['name'] = [a.name for a in assignments]
    canvas_assignments['id'] = [a.id for a in assignments]

    return canvas_assignments

