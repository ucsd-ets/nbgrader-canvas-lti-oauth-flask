from nbgrader_to_canvas.canvas import CanvasWrapper
from flask import Blueprint, Response, render_template, session, request
from pylti.flask import lti

from . import app
from .utils import return_error

from nbgrader.api import Gradebook


grade_students_blueprint = Blueprint('grade_students', __name__)

# grade assignments
@grade_students_blueprint.route("/grade_students", methods=['GET'], strict_slashes=False)
def grade_students():
    """
    Returns the lti.grading_list file for the app.
    grading_list can be built at https://www.eduappcenter.com/
    """
    try:
        students = get_students()
        return Response(
            render_template('students.htm.j2', std=students)
        )
    except Exception as e:
        app.logger.error(e)
        import os
        app.logger.error(os.getcwd())
        app.logger.error("No students file.")
        msg = (
            'Issue with the students file. Please refresh and try again. '
            'If this error persists, please contact support.'
        )
        return return_error(msg)


@lti(request='session', role='staff')
def get_students(lti=lti):
    """
    Get all the Canvas Assignments from the course
    """
    # get the course id
    course_id = session['course_id']

    # initialize a new canvasapi Canvas object
    canvas_wrapper = CanvasWrapper()
    canvas = canvas_wrapper.get_canvas()

    # get canvas assignments from course
    course = canvas.get_course(course_id)
    students = course.get_students()

    # split the name and id for each course assignment
    canvas_students = {}
    canvas_students['name'] = [a.name for a in assignments]
    canvas_students['id'] = [a.id for a in assignments]

    return canvas_students
