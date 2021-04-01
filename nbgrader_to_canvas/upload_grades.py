from types import GetSetDescriptorType
from flask import Blueprint, render_template, session, request, redirect, url_for
from pylti.flask import lti

from .utils import get_canvas, error
from . import app
from . import settings
from nbgrader.api import Gradebook, MissingEntry

import json
import logging
import sys
import jsonpickle
upload_grades_blueprint = Blueprint('upload_grades', __name__)

# Web Views / Routes
@upload_grades_blueprint.route('/upload_grades', methods=['GET', 'POST'])
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

    # TODO: modify below to redirect to status page after POST, see
    # https://stackoverflow.com/questions/31542243/redirect-to-other-view-after-submitting-form

    args = request.args.to_dict()

    course_id = session['course_id']

    # initialize a new canvasapi Canvas object
    canvas = get_canvas()

    # canvasapi debugging info https://github.com/ucfopen/canvasapi/blob/master/docs/debugging.rst
    canvasapi_logger = logging.getLogger("canvasapi")
    canvasapi_handler = logging.StreamHandler(sys.stdout)
    canvasapi_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    canvasapi_handler.setLevel(logging.ERROR)
    canvasapi_handler.setFormatter(canvasapi_formatter)
    canvasapi_logger.addHandler(canvasapi_handler)
    canvasapi_logger.setLevel(logging.ERROR)

    # to do error handling
    #if canvas is None:
    #    courses = None
    #else:
    #    courses = canvas.get_courses()
    app.logger.setLevel(logging.DEBUG)
    app.logger.info("request.method:")
    app.logger.info(request.method)

    # progress object status types: the state of the job one of 'queued', 'running', 'completed', 'failed'


    # ADD JS TO VIEW:
    # 1) every 10 seconds, update the status of any assignments in the UI that have a status of queued or running in sqlalchemy assignments_table
    #    a) fetch the url from the sqlalchemy assignments_table, get the status
    # 2) if status is different than status in db, update db and UI with this new value 

    # POST: 
    # 1) submit assignment using submissions_bulk_update
    #    a) find the nbgrader assignment by name
    # 2) insert/update sqlalchemy assignment_match table for the submitted nbgrader assignment:
    #    a) if nbgrader assignment does not exist: insert row with matching nbgrader/canvas assignment IDs, upload progress ID and upload status string
    #    b) if it does: 
    if request.method == 'POST':


        #
        # get canvas info
        #
        course = canvas.get_course(course_id)
        canvas_assignments = course.get_assignments()
        canvas_users = course.get_users()
        
        canvas_students = {}
        # TODO: modify to only get active users
        for canvas_user in canvas_users:
            if hasattr(canvas_user, "login_id") and canvas_user.login_id is not None:
                canvas_students[canvas_user.login_id]=canvas_user.id  
                
                app.logger.debug("canvas user login id:")
                app.logger.debug(canvas_user.login_id)   
                app.logger.debug("canvas user id:")
                app.logger.debug(canvas_user.id)   

        #
        # get nbgrader info
        #

        with Gradebook("sqlite:////mnt/nbgrader/TEST_NBGRADER/grader/gradebook.db") as gb:
        #with Gradebook("sqlite:////mnt/nbgrader/BIPN162_S120_A00/grader/gradebook.db") as gb:

            # create a list of dictionaries for each submission
            #nb_assignments = gb.assignments
            # TODO: change from hardcoded assignment string to the POST assignment_name parameter
            # TODO: handle exception here
            nb_assignment = gb.find_assignment("assign 1")

            # can we change this to just get the students for this assignment?
            nb_students = gb.students
            
            app.logger.debug("nb assignment name:")
            app.logger.debug(nb_assignment.name)
            
            nb_grade_data = {}

            # loop over each nb student
            for nb_student in nb_students:

                app.logger.debug("student id:")
                app.logger.debug(nb_student.id)

                # ceate dict for grade_data, with nested dict {student id: {score}}
                nb_student_and_score = {}            

                # Try to find the submission in the nbgrader database. If it doesn't exist, the
                # MissingEntry exception will be raised and we assign them a score of None.

                try:
                    nb_submission = gb.find_submission(nb_assignment.name, nb_student.id)
                except MissingEntry:
                    nb_student_and_score['posted_grade'] = None
                else:
                    nb_student_and_score["posted_grade"] = nb_submission.score
                    app.logger.debug("sub name:")
                    app.logger.debug(nb_submission.name)
                    app.logger.debug("sub id:")
                    app.logger.debug(nb_submission.id)
                    app.logger.debug("sub score:")
                    app.logger.debug(nb_submission.score)

                # student.id will give us student's username, ie shrakibullah. we will need to compare this to
                # canvas's login_id instead of user_id

                # TEMP HACK: e7li and shrakibullah are instructors; change their ids (after 
                # submission fetch above) here to students in canvas course
                # TODO: create submissions for canvas course students
                temp_nb_student_id = nb_student.id
                if nb_student.id == 'e7li':
                    temp_nb_student_id = 'testacct222'
                if nb_student.id == 'shrakibullah':
                    temp_nb_student_id = 'testacct333'                    

                # convert nbgrader username to canvas id (integer)
                #canvas_student_id = canvas_students[nb_student.id]
                canvas_student_id = canvas_students[temp_nb_student_id]
                nb_grade_data[canvas_student_id] = nb_student_and_score

            # end nbgrader student loop

            # TODO: skip over canvas assignment loop if we already have canvas_assignment.id in our sqlachemy assignments table (re-submission?)

            # loop over canvas assignments, upload submissions if name matches
            # TODO: check for dup assignment names
            for canvas_assignment in canvas_assignments:
                if nb_assignment.name == canvas_assignment.name:
                    app.logger.debug("canvas assignment name match; id:")
                    app.logger.debug(canvas_assignment.id)
                    app.logger.debug("canvas assignment name match; name:")
                    app.logger.debug(canvas_assignment.name)
                    app.logger.debug("upload submissions for existing canvas assignment")
                    app.logger.debug("grade data to upload:")
                    app.logger.debug(nb_grade_data)

                    assignment_to_upload = course.get_assignment(canvas_assignment.id)                

                    # TODO: check if published, if not, publish?
                    progress = assignment_to_upload.submissions_bulk_update(grade_data=nb_grade_data)
                    progress = progress.query()
                    session['progress_json']=jsonpickle.encode(progress)
                    session.modified=True
                # end assignment names match
            # end canvas assignment loop
        # end with gradebook
    # end if POST

    # GET (and POST): 
    # 1) get list of canvas assignments in the "assignments group" for course via canvasapi 
    #    wrapper version of https://canvas.instructure.com/doc/api/assignment_groups.html; use this to populate canvas assignment dropdown lists in UI
    # 2) query nbgrader db, populate list of nbgrader assignments
    # 3) display a UI table where each row is an nbgrader assignment
    # 4) for each nbgrader assignment, check the sqlalchemy assignment_match table to see if there's an entry (which means it has a corresponding canvas assignment)
    #   a) if there is: set the corresponding canvas assignment in the dropdown in the second column of page
    #   b) if there isn't: populate dropdown with canvas assignments that do not exist in sqlalchemy db table of matched assignments. set the dropdown to "create in canvas with same name" initially.
    # 5) for each nbgrader assignment, indicate the status under the submit button for each assignment. 
    #   a) if status in sqlachemy assignment_match table is complete/, show status as complete
    #   b) if not complete: get the progress url from that db row, fetch the url using js, display the status (percent complete) below the button

    return render_template('upload_grades.htm.j2', progress=None, BASE_URL=settings.BASE_URL)
