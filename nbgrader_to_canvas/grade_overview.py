from flask import Blueprint, Response, render_template, session, request, url_for
from pylti.flask import lti

from . import app
from .utils import get_canvas, return_error

from nbgrader.api import Gradebook
from .models import AssignmentMatch

import time

grade_overview_blueprint = Blueprint('grade_overview', __name__)

# grade_overview
@grade_overview_blueprint.route("/grade_overview", methods=['GET', 'POST'], strict_slashes=False)
def grade_overview():
    """
    Returns the overview file for the app.
    grade_overview can be viewed at overview.htm.j2
    """

    try:
        nb_assignments = get_nbgrader_assignments()
        course_id = get_canvas_id()
        canvas_assignments, group = get_canvas_assignments(course_id)
        db_matches = match_assignments(nb_assignments, course_id)
        
        return Response(
            render_template('overview.htm.j2', course_id=course_id, nb_assign=nb_assignments,
                            cv_assign=canvas_assignments, db_matches=db_matches, progress=None)
        )

    except Exception as e:
        app.logger.error(e)
        import os
        app.logger.error(os.getcwd())
        app.logger.error("Overview file error.")
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
def get_canvas_id(lti=lti):
    """
    Get the canvas course id
    """
    return session['course_id']


def get_canvas_assignments(course_id):
    """
    Get the assignments for the Canvas course
    """
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

    # have the id:name key,value pair for each course assignment
    canvas_assignments = {a.id:a.name for a in assignments}
    # app.logger.debug("canvas_assign: ")
    # app.logger.debug(canvas_assignments)

    return canvas_assignments, group.id
    

def match_assignments(nb_assignments, course_id):
    """
    Check sqlalchemy table for match with nbgrader assignments from a specified course. Creates a dictionary with nbgrader
        assignments as the key
    If match is found, query the entry from the table and set as the value.
    Else, set the value to None
    """
    nb_matches = {assignment.name:AssignmentMatch.query.filter_by(nbgrader_name=assignment.name, course_id=course_id).first()
                                                            for assignment in nb_assignments}
    # app.logger.debug("nb_match: ")
    # app.logger.debug(nb_matches)
    return nb_matches