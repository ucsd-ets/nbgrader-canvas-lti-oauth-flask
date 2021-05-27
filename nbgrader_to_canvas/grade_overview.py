from flask import Blueprint, Response, render_template, session, request, url_for, redirect
from pylti.flask import lti

import os


from . import app
from .utils import get_canvas, return_error, error

from nbgrader.api import Gradebook
from .models import AssignmentMatch

from canvasapi.exceptions import InvalidAccessToken
from .upload_grades import upload_grades

import time

grade_overview_blueprint = Blueprint('grade_overview', __name__)


@grade_overview_blueprint.route("/grade_overview", methods=['GET', 'POST'])
def grade_overview(progress = None):
    """
    Renders the main template for the flask application.
    grade_overview can be viewed at overview.htm.j2
    """

    try:
        nb_assignments = get_nbgrader_assignments()
        course_id = get_canvas_id()
        group = get_assignment_group_id()
        canvas_assignments = get_canvas_assignments(course_id, group)


        if request.method == 'POST':
            progress = upload_grades(course_id, group)
            return redirect(url_for('grade_overview.grade_overview'))

        db_matches = match_assignments(nb_assignments, course_id)

        return Response(
            render_template('overview.htm.j2',  nb_assign=nb_assignments, cv_assign=canvas_assignments,
                             db_matches=db_matches, progress = progress)
        )

    except KeyError as keyE:
        app.logger.error("KeyError: " + str(keyE))
        app.logger.error(os.getcwd())

        msg = (
            'Issues with querying the database for the canvas_user_id. '
            'Cannot call functions on the canvas object. '
            'Delete user from users table or wait for token refresh'
        )
        return return_error(msg)

    except InvalidAccessToken as eTok:
        app.logger.error("InvalidAccessToken: " + str(eTok))
        app.logger.error(os.getcwd())

        msg = (
            'Issues with access token.'
        )
        return return_error(msg)

    except Exception as e:
        app.logger.error("Exception: " + str(type(e)) + str(e))
        app.logger.error(os.getcwd())
        app.logger.error(str(type(e)) + " error occurred.")
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


def get_assignment_group_id():

    # initialize a new canvasapi Canvas object
    canvas = get_canvas()
    
    # find the "Assignments" group
    course = canvas.get_course(get_canvas_id())
    assignment_groups = course.get_assignment_groups()

    for ag in assignment_groups:
        if (ag.name == "Assignments"):
            return course.get_assignment_group(ag.id).id


def get_canvas_assignments(course_id, group):
    """
    Get the assignments for the Canvas course
    """
    # initialize a new canvasapi Canvas object
    canvas = get_canvas()

    # get canvas assignment groups from course
    course = canvas.get_course(course_id)
    assignments = course.get_assignments_for_group(group)

    # have the id:name key:value pair for each course assignment
    canvas_assignments = {a.id:a.name for a in assignments}

    return canvas_assignments
    

def match_assignments(nb_assignments, course_id):
    """
    Check sqlalchemy table for match with nbgrader assignments from a specified course. Creates a dictionary with nbgrader
        assignments as the key
    If match is found, query the entry from the table and set as the value.
    Else, set the value to None
    """
    nb_matches = {assignment.name:AssignmentMatch.query.filter_by(nbgrader_assign_name=assignment.name, course_id=course_id).first()
                                                            for assignment in nb_assignments}
    return nb_matches