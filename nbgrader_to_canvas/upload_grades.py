from types import GetSetDescriptorType
from flask import Blueprint, render_template, session, request, redirect, url_for
from pylti.flask import lti

from .utils import get_canvas, error
from . import app, db
from . import settings
from nbgrader.api import Gradebook, MissingEntry
from .models import AssignmentMatch

import datetime
import requests

import json
import logging
import sys
import jsonpickle

import sys
import os
import canvasapi
import pytest
#  Import the Canvas class
from canvasapi.assignment import (
    Assignment,
    AssignmentGroup,
    AssignmentOverride,
    AssignmentExtension,
)
from canvasapi.progress import Progress
from canvasapi.course import Course

upload_grades_blueprint = Blueprint('upload_grades', __name__)

# Web Views / Routes
@upload_grades_blueprint.route('/upload_grades', methods=['GET', 'POST'])
@lti(error=error, request='session', role='staff', app=app)
def upload_grades(course_id, group, course_name="TEST_NBGRADER", lti=lti):
      
    

    # TODO: modify below to redirect to status page after POST, see
    # https://stackoverflow.com/questions/31542243/redirect-to-other-view-after-submitting-form

    args = request.args.to_dict()

    # initialize a new canvasapi Canvas object
    canvas = get_canvas()
    course = canvas.get_course(course_id)

    progress = None

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
    app.logger.debug("request.method:")
    app.logger.debug(request.method)

    #
    # get assignment match info from psql table
    # TODO: fetch for all
    #assignment_match = Users.query.filter_by(user_id=int(session['canvas_user_id'])).first()

    # ADD JS TO VIEW:
    # 1) every 10 seconds, update the status of any assignments in the UI that have a status of queued or running in sqlalchemy assignments_table
    #    a) fetch the progress url from the sqlalchemy assignments_table, get the status
    # 2) if status is different than status in db, update db and UI with this new value 

    # POST: 
    # 1) submit assignment using submissions_bulk_update
    #    a) find the nbgrader assignment by name
    # 2) insert/update sqlalchemy assignment_match table for the submitted nbgrader assignment:
    #    a) if nbgrader assignment does not exist: insert row with matching nbgrader/canvas assignment IDs, upload progress object url (progress.url) 
    #       and upload status string
    #    b) if it does: check that the canvas assignment id they submitted matches the one in the db.  if it doesn't, return an error.  update the
    #       row with the new progress object url and progress object status (progress.status)
    #       progress object status types: the state of the job one of 'queued', 'running', 'completed', 'failed'

    if request.method == 'POST':
        canvas_assignment_id = None
        assignment_to_upload = None

        app.logger.debug("form_nb_assign_name:")
        app.logger.debug(request.form.get('form_nb_assign_name'))
        app.logger.debug("form_canvas_assign_id:")
        app.logger.debug(request.form.get('form_canvas_assign_id'))

        form_nb_assign_name = request.form.get('form_nb_assign_name')
        form_canvas_assign_id = request.form.get('form_canvas_assign_id')

        assignment_match = AssignmentMatch.query.filter_by(nbgrader_assign_name=form_nb_assign_name, course_id=course_id).first()
        app.logger.debug("assignment match:")
        app.logger.debug(assignment_match)
        # app.logger.debug("assignment match url:")
        # app.logger.debug(assignment_match.progress_url)
        # upload_url=assignment_match.progress_url
        
        canvas_users = course.get_users()        
        canvas_students = {}
        # TODO: modify to only get active users
        for canvas_user in canvas_users:
            if hasattr(canvas_user, "login_id") and canvas_user.login_id is not None:
                canvas_students[canvas_user.login_id]=canvas_user.id  
                
                # app.logger.debug("canvas user login id:")
                #app.logger.debug(canvas_user.login_id)   
                #app.logger.debug("canvas user id:")
                #app.logger.debug(canvas_user.id)   

        #
        #  get nbgrader info
        #

        with Gradebook("sqlite:////mnt/nbgrader/"+course_name+"/grader/gradebook.db") as gb:
        #with Gradebook("sqlite:////mnt/nbgrader/BIPN162_S120_A00/grader/gradebook.db") as gb:

            # get the nbgrader assignment from the nbgradebook for the 
            # nbgrader assignment submitted in the form
            # TODO: handle exception here
            nb_assignment = gb.find_assignment(form_nb_assign_name)

            # TODO: can we change this to just get the students for this assignment?
            nb_students = gb.students            
            nb_grade_data = {}

            # loop over each nb student
            for nb_student in nb_students:

                #app.logger.debug("student id:")
                #app.logger.debug(nb_student.id)

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

            # TODO: if we have an entry in our assignment match table for this nbgrader assignment,
            # check if its respective canvas assignment matches what came from the form.  if it doesn't,
            # instrutor has changed the association, post an error message and bail out

            #  if we're creating a new canvas assignment
            if (form_canvas_assign_id == 'create') :
                app.logger.debug("upload submissions for non-existing canvas assignment; will be named:")
                app.logger.debug(form_nb_assign_name)                

                # create new assignments as published
                assignment_to_upload = course.create_assignment({'name':form_nb_assign_name, 'published':'true', 'assignment_group_id':group})
                canvas_assignment_id = assignment_to_upload.id

            #  if we're uploading to an existing canvas assignment
            else:
                # get the id of the canvas assignment for the canvas assignment name that was submitted
                app.logger.debug("upload submissions for existing canvas assignment;")
                assignment_to_upload = course.get_assignment(form_canvas_assign_id)
                canvas_assignment_id = form_canvas_assign_id           

            # TODO: check if assignment is published, if not, publish?
            # submit assignment
            progress = assignment_to_upload.submissions_bulk_update(grade_data=nb_grade_data)
            progress = progress.query()
            session['progress_json'] = jsonpickle.encode(progress)
            session.modified=True
            app.logger.debug("progress url:")
            app.logger.debug(progress.url)
            # app.logger.debug("progress json:")
            # app.logger.debug(session['progress_json'])

            # check if row exists in assignment match table
            if assignment_match:
                app.logger.debug("Updating assignment in database")
                assignment_match.progress_url = progress.url
                assignment_match.last_updated_time = progress.updated_at
            else:
                app.logger.debug("Creating new assignment in database")
                newMatch = AssignmentMatch(course_id=course_id, nbgrader_assign_name=form_nb_assign_name,
                            canvas_assign_id=canvas_assignment_id, upload_progress_url=progress.url, last_updated_time=progress.updated_at)
                db.session.add(newMatch)
            
            db.session.commit()


            # TODO: insert/update row in assignment match table
        # end with gradebook
    # end if POST

    # GET (and POST): 
    # 1) get list of canvas assignments in the "assignments group" for course via canvasapi 
    #    wrapper version of https://canvas.instructure.com/doc/api/assignment_groups.html; use this to populate canvas assignment dropdown lists in UI
    # 2) query nbgrader db, populate list of nbgrader assignments
    # 3) display a UI table where each row is an nbgrader assignment
    # 4) for each nbgrader assignment, check the sqlalchemy assignment_match table to see if there's an entry (which means it has a corresponding canvas assignment)
    #   a) if there is: set the corresponding canvas assignment in the dropdown in the second column of page, make the other canvas assignments un-selectable.
    #      to make dropdown items unselectable, use javascript after page onload() or similar
    #   b) if there isn't: populate dropdown with canvas assignments that do not exist in sqlalchemy db table of matched assignments. set the dropdown to "create in canvas with same name" initially.
    # 5) for each nbgrader assignment, indicate the status under the submit button for each assignment. 
    #   a) if status in sqlachemy assignment_match table is complete/, show status as complete
    #   b) if not complete: get the progress url from that db row, fetch the url using js, display the status (percent complete) below the button


    # TODO: query sqlalchemy assignment_match table to do #4, #5 above

    return progress
    # return render_template('upload_grades.htm.j2', nb_assign=nb_assign, cv_assign=cv_assign, progress=progress, 
    #     upload_progress_url=upload_progress_url,upload_progress_assignment=upload_progress_assignment)
    # return render_template('overview.htm.j2', nb_assign=nb_assign, cv_assign=cv_assign, db_matches=db_matches,
                        #  progress = progress)


@app.route('/get_progress', methods=['GET'])
def get_progress():

    """
    Endpoint to call from JS. queries the database for a specified assignment and returns the upload
    url for the assignment as a JSON.

    If no match is in the database, it returns null to JS.
    """
    
    # get assignment and course for db query
    assignment = request.args.get('assignment')
    id = request.args.get('course_id')

    if request.method == 'GET':
        match = AssignmentMatch.query.filter_by(nbgrader_assign_name=assignment, course_id=int(id)).first()

        # if match found, return db upload url as a json
        if match:
            app.logger.debug("found match")
            return requests.get(match.upload_progress_url).json()

        # if match not found, return null
        else:
            app.logger.debug("didn't find match")
            return json.dumps(match)

# def format_time(datetime):

#     months = {'01':'Jan', '02':'Feb', '03':'Mar', '04':'Apr', '05':'May', '06':'Jun',
# 		      '07':'Jul', '08':'Aug', '09':'Sep', '10':'Oct', '11':'Nov', '12':'Dec'}

#     date, time = datetime.split("T")
#     date = date.split("-")
#     time = list(map(int, time.strip("Z").split("-")))
    
#     time[0] = time[0] - 
#     if time[0] // 12 == 1:
#         time[2] = "pm"
#     else:
#         time[2] = "am"
    
#     if time[0] == ""


#     return "{0} {1} at {2}:{3}{4}".format(months[date[1]], date[2], time[0], time[1], time[2])





def _upload_grades(course_id, group, course_name="TEST_NBGRADER", lti=lti):
    '''
    Step 1: Initialize course object
    Step 2: Parse out the form data
    Step 3: Modify database?
    '''
def init_course(course_id):
    canvas = get_canvas()
    course = canvas.get_course(course_id)
    return course
