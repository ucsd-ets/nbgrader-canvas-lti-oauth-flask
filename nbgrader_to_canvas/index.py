from flask import Blueprint, render_template, session, request
from pylti.flask import lti

from .utils import get_canvas, error
from . import app
from . import settings
from nbgrader.api import Gradebook, MissingEntry


index_blueprint = Blueprint('index', __name__)

# Web Views / Routes
@index_blueprint.route('/index', methods=['GET'])
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

    #
    # nbgrader code
    #

    with Gradebook("sqlite:///../gradebook.db") as gb:

        # create a list of dictionaries for each submission
        nb_assignments = gb.assignments
        nbgraderdata = {}


        # create a list of assignments or students to grade
        # if lists are empty, all students are selected
        # NEED to find a way to populate this - most likely on flask application?? #
        assignmentList = []
        studentList = []

        # loop over all assignments
        for assignment in gb.assignments:
            grade_data = {}

            # only continue if assignment is required
            if assignmentList and assignment.name not in assignmentList:
                continue

            # loop over each student
            for student in gb.students:

                # only continue if student is required
                if studentList and student.id not in studentList:
                    continue

                # ceate dict for grade_data, with nested dict {student id: {score}}
                student_and_score = {}            

                # Try to find the submission in the database. If it doesn't exist, the
                # MissingEntry exception will be raised and we assign them a score of None.

                try:
                    submission = gb.find_submission(assignment.name, student.id)
                except MissingEntry:
                    student_and_score['posted_grade'] = None
                else:
                    student_and_score["posted_grade"] = submission.score

                # student.id will give us student's username, ie shrakibullah. we will need to compare this to
                # canvas's login_id instead of user_id
                grade_data[student.id] = student_and_score

            nbgraderdata[assignment] = grade_data




    # initialize a new canvasapi Canvas object
    canvas = get_canvas()

    if canvas is None:
        courses = None
    else:
        courses = canvas.get_courses()
    
    return render_template('index.htm.j2', nbgraderdata=nbgraderdata, msg=msg, course_id=session['course_id'],all_courses=courses, BASE_URL=settings.BASE_URL)
