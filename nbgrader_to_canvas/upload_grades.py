from types import GetSetDescriptorType
from flask import Blueprint, render_template, session, request, redirect, url_for
from pylti.flask import lti

from .utils import error
from . import app, db
from . import settings
from nbgrader.api import Gradebook, MissingEntry
from .models import AssignmentMatch
from .canvas import CanvasWrapper

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
import time
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
# @upload_grades_blueprint.route('/upload_grades', methods=['GET', 'POST'])
# @lti(error=error, request='session', role='staff', app=app)
# def upload_grades(course_id, group, course_name="TEST_NBGRADER", lti=lti):


#     # TODO: modify below to redirect to status page after POST, see
#     # https://stackoverflow.com/questions/31542243/redirect-to-other-view-after-submitting-form

#     args = request.args.to_dict()

#     app.logger.info("course_id: {}".format(course_id))
#     app.logger.info("group: {}".format(group))

#     # initialize a new canvasapi Canvas object
#     canvas = get_canvas()
#     course = canvas.get_course(course_id)

#     app.logger.info("course: {}".format(course))

#     progress = None

#     # canvasapi debugging info https://github.com/ucfopen/canvasapi/blob/master/docs/debugging.rst
#     canvasapi_logger = logging.getLogger("canvasapi")
#     canvasapi_handler = logging.StreamHandler(sys.stdout)
#     canvasapi_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

#     canvasapi_handler.setLevel(logging.ERROR)
#     canvasapi_handler.setFormatter(canvasapi_formatter)
#     canvasapi_logger.addHandler(canvasapi_handler)
#     canvasapi_logger.setLevel(logging.ERROR)

#     # to do error handling
#     #if canvas is None:
#     #    courses = None
#     #else:
#     #    courses = canvas.get_courses()
#     app.logger.setLevel(logging.DEBUG)
#     app.logger.debug("request.method:")
#     app.logger.debug(request.method)

#     #
#     # get assignment match info from psql table
#     # TODO: fetch for all
#     #assignment_match = Users.query.filter_by(user_id=int(session['canvas_user_id'])).first()

#     # ADD JS TO VIEW:
#     # 1) every 10 seconds, update the status of any assignments in the UI that have a status of queued or running in sqlalchemy assignments_table
#     #    a) fetch the progress url from the sqlalchemy assignments_table, get the status
#     # 2) if status is different than status in db, update db and UI with this new value 

#     # POST: 
#     # 1) submit assignment using submissions_bulk_update
#     #    a) find the nbgrader assignment by name
#     #
#     # 2) insert/update sqlalchemy assignment_match table for the submitted nbgrader assignment:
#     #    a) if nbgrader assignment does not exist: insert row with matching nbgrader/canvas assignment IDs, upload progress object url (progress.url) 
#     #       and upload status string
#     #    b) if it does: check that the canvas assignment id they submitted matches the one in the db.  if it doesn't, return an error.  update the
#     #       row with the new progress object url and progress object status (progress.status)
#     #       progress object status types: the state of the job one of 'queued', 'running', 'completed', 'failed'

#     if request.method == 'POST':
#         canvas_assignment_id = None
#         assignment_to_upload = None

#         app.logger.debug("form_nb_assign_name:")
#         app.logger.debug(request.form.get('form_nb_assign_name'))
#         app.logger.debug("form_canvas_assign_id:")
#         app.logger.debug(request.form.get('form_canvas_assign_id'))

#         form_nb_assign_name = request.form.get('form_nb_assign_name')
#         form_canvas_assign_id = request.form.get('form_canvas_assign_id')

#         assignment_match = AssignmentMatch.query.filter_by(nbgrader_assign_name=form_nb_assign_name, course_id=course_id).first()
#         app.logger.debug("assignment match:")
#         app.logger.debug(assignment_match)
#         # app.logger.debug("assignment match url:")
#         # app.logger.debug(assignment_match.progress_url)
#         # upload_url=assignment_match.progress_url
        
#         canvas_users = course.get_users()        
#         canvas_students = {}
#         # TODO: modify to only get active users
#         for canvas_user in canvas_users:
#             if hasattr(canvas_user, "login_id") and canvas_user.login_id is not None:
#                 canvas_students[canvas_user.login_id]=canvas_user.id  
                
#                 # app.logger.debug("canvas user login id:")
#                 # app.logger.debug(canvas_user.login_id)   
#                 # app.logger.debug("canvas user id:")
#                 # app.logger.debug(canvas_user.id)   

#         #
#         #  get nbgrader info
#         #

#         with Gradebook("sqlite:////mnt/nbgrader/"+course_name+"/grader/gradebook.db") as gb:
#         #with Gradebook("sqlite:////mnt/nbgrader/BIPN162_S120_A00/grader/gradebook.db") as gb:

#             # get the nbgrader assignment from the nbgradebook for the 
#             # nbgrader assignment submitted in the form
#             # TODO: handle exception here
#             nb_assignment = gb.find_assignment(form_nb_assign_name)

#             # TODO: can we change this to just get the students for this assignment?
#             nb_students = gb.students            
#             nb_grade_data = {}

#             # loop over each nb student
#             for nb_student in nb_students:

#                 #app.logger.debug("student id:")
#                 #app.logger.debug(nb_student.id)

#                 # ceate dict for grade_data, with nested dict {student id: {score}}
#                 nb_student_and_score = {}            

#                 # Try to find the submission in the nbgrader database. If it doesn't exist, the
#                 # MissingEntry exception will be raised and we assign them a score of None.

#                 try:
#                     nb_submission = gb.find_submission(nb_assignment.name, nb_student.id)
#                 except MissingEntry:
#                     nb_student_and_score['posted_grade'] = None
#                 else:
#                     nb_student_and_score["posted_grade"] = nb_submission.score

#                 # student.id will give us student's username, ie shrakibullah. we will need to compare this to
#                 # canvas's login_id instead of user_id

#                 # TEMP HACK: e7li and shrakibullah are instructors; change their ids (after 
#                 # submission fetch above) here to students in canvas course
#                 # TODO: create submissions for canvas course students
#                 temp_nb_student_id = nb_student.id
#                 if nb_student.id == 'e7li':
#                     temp_nb_student_id = 'testacct222'
#                 if nb_student.id == 'shrakibullah':
#                     temp_nb_student_id = 'testacct333'                    

#                 # convert nbgrader username to canvas id (integer)
#                 #canvas_student_id = canvas_students[nb_student.id]
#                 canvas_student_id = canvas_students[temp_nb_student_id]
#                 nb_grade_data[canvas_student_id] = nb_student_and_score

#             # end nbgrader student loop

#             # TODO: if we have an entry in our assignment match table for this nbgrader assignment,
#             # check if its respective canvas assignment matches what came from the form.  if it doesn't,
#             # instrutor has changed the association, post an error message and bail out

#             #  if we're creating a new canvas assignment
#             try:
#                 app.logger.debug("upload submissions for existing canvas assignment;")
#                 assignment_to_upload = course.get_assignment(form_canvas_assign_id)
#                 app.logger.debug("assignment: {}".format(assignment_to_upload))
#                 canvas_assignment_id = form_canvas_assign_id     
#             except:
#                 app.logger.debug("upload submissions for non-existing canvas assignment; will be named: {}".format(form_nb_assign_name))
#                 app.logger.debug("Group: {}".format(group))  

#                 # create new assignments as published
#                 assignment_to_upload = course.create_assignment({'name':form_nb_assign_name, 'published':'true', 'assignment_group_id':group})
#                 canvas_assignment_id = assignment_to_upload.id
#                 app.logger.debug("assignment: {}".format(assignment_to_upload.name))
#                 app.logger.debug("id: {}".format(canvas_assignment_id))

#             # if (form_canvas_assign_id == 'create') :
#             #     app.logger.debug("upload submissions for non-existing canvas assignment; will be named: {}".format(form_nb_assign_name))
#             #     app.logger.debug("Group: {}".format(group))  

#             #     # create new assignments as published
#             #     assignment_to_upload = course.create_assignment({'name':form_nb_assign_name, 'published':'true', 'assignment_group_id':group})
#             #     canvas_assignment_id = assignment_to_upload.id
#             #     app.logger.debug("assignment: {}".format(assignment_to_upload))
#             #     app.logger.debug("id: {}".format(canvas_assignment_id))

#             # #  if we're uploading to an existing canvas assignment
#             # else:
#             #     # get the id of the canvas assignment for the canvas assignment name that was submitted
#             #     app.logger.debug("upload submissions for existing canvas assignment;")
#             #     assignment_to_upload = course.get_assignment(form_canvas_assign_id)
#             #     app.logger.debug("assignment: {}".format(assignment_to_upload))
#             #     canvas_assignment_id = form_canvas_assign_id           

#             # TODO: check if assignment is published, if not, publish?
#             # submit assignment
#             progress = assignment_to_upload.submissions_bulk_update(grade_data=nb_grade_data)
#             progress = progress.query()
#             session['progress_json'] = jsonpickle.encode(progress)
#             session.modified=True
#             app.logger.debug("progress url:")
#             app.logger.debug(progress.url)

#             # check if row exists in assignment match table
#             if assignment_match:
#                 app.logger.debug("Updating assignment in database")
#                 assignment_match.progress_url = progress.url
#                 assignment_match.last_updated_time = progress.updated_at
#             else:
#                 app.logger.debug("Creating new assignment in database")
#                 newMatch = AssignmentMatch(course_id=course_id, nbgrader_assign_name=form_nb_assign_name,
#                             canvas_assign_id=canvas_assignment_id, upload_progress_url=progress.url, last_updated_time=progress.updated_at)
#                 app.logger.debug(newMatch)
#                 db.session.add(newMatch)
            
#             db.session.commit()


#             # TODO: insert/update row in assignment match table
#         # end with gradebook
#     # end if POST

#     # GET (and POST): 
#     # 1) get list of canvas assignments in the "assignments group" for course via canvasapi 
#     #    wrapper version of https://canvas.instructure.com/doc/api/assignment_groups.html; use this to populate canvas assignment dropdown lists in UI
#     # 2) query nbgrader db, populate list of nbgrader assignments
#     # 3) display a UI table where each row is an nbgrader assignment
#     # 4) for each nbgrader assignment, check the sqlalchemy assignment_match table to see if there's an entry (which means it has a corresponding canvas assignment)
#     #   a) if there is: set the corresponding canvas assignment in the dropdown in the second column of page, make the other canvas assignments un-selectable.
#     #      to make dropdown items unselectable, use javascript after page onload() or similar
#     #   b) if there isn't: populate dropdown with canvas assignments that do not exist in sqlalchemy db table of matched assignments. set the dropdown to "create in canvas with same name" initially.
#     # 5) for each nbgrader assignment, indicate the status under the submit button for each assignment. 
#     #   a) if status in sqlachemy assignment_match table is complete/, show status as complete
#     #   b) if not complete: get the progress url from that db row, fetch the url using js, display the status (percent complete) below the button


#     # TODO: query sqlalchemy assignment_match table to do #4, #5 above

#     return progress
#     # return render_template('upload_grades.htm.j2', nb_assign=nb_assign, cv_assign=cv_assign, progress=progress, 
#     #     upload_progress_url=upload_progress_url,upload_progress_assignment=upload_progress_assignment)
#     # return render_template('overview.htm.j2', nb_assign=nb_assign, cv_assign=cv_assign, db_matches=db_matches,
#                         #  progress = progress)


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
            app.logger.debug("found match: {}, {}, {}".format(match.canvas_assign_id, assignment, id))
            #app.logger.debug("{}".format(requests.get(match.upload_progress_url).json()))
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
@upload_grades_blueprint.route('/upload_grades', methods=['GET', 'POST'])
@lti(error=error, request='session', role='staff', app=app)
def upload_grades(course_id, group, course_name="TEST_NBGRADER", lti=lti):
    #If not posting, don't upload anything
    if not request.method == "POST":
        return None
    app.logger.debug("form_nb_assign_name:")
    app.logger.debug(request.form.get('form_nb_assign_name'))
    app.logger.debug("form_canvas_assign_id:")
    app.logger.debug(request.form.get('form_canvas_assign_id'))

    form_canvas_assign_id = request.form.get('form_canvas_assign_id') 
    form_nb_assign_name = request.form.get('form_nb_assign_name')
    
    uploader = UploadGrades(course_id, group, form_canvas_assign_id, form_nb_assign_name, course_name, lti)
    uploader.init_course()
    uploader.parse_form_data()
    return uploader.update_database()


class UploadGrades:

    def __init__(self, course_id, group, form_canvas_assign_id, form_nb_assign_name, course_name="TEST_NBGRADER", lti=lti):
       
        self._course_id = course_id
        self._group = group
        self._form_canvas_assign_id = form_canvas_assign_id
        self._form_nb_assign_name = form_nb_assign_name
        self._course_name = course_name
        self._lti = lti

        self._setup_canvasapi_debugging()   

    # Returns a course object corresponding to given course_id
    # TEST: param is to allow testing
    def init_course(self, flask_session = session):
        canvas_wrapper = CanvasWrapper(settings.API_URL, flask_session)
        canvas = canvas_wrapper.get_canvas()
        self._course = canvas.get_course(self._course_id)
        if self._course is None:
            raise Exception('Invalid course id')
    
    def parse_form_data(self):
        canvas_students = self._get_canvas_students()
        self.student_grades = self._get_student_grades(canvas_students)

        if (self._form_canvas_assign_id == 'create'):
            max_score = self._get_max_score()
            self.assignment_to_upload = self._create_assignment(max_score)
        else: 
            self.assignment_to_upload = self._get_assignment()

        self.canvas_assignment_id = self.assignment_to_upload.id
    
    # Submits grades to canvas, and creates/updates the AssignmentMatch database for the assignment
    def update_database(self):
        progress = self._submit_grades()
        assignment_match = AssignmentMatch.query.filter_by(nbgrader_assign_name=self._form_nb_assign_name, course_id=self._course_id).first()
        if assignment_match:
            self._update_match(assignment_match, progress)
        else:
            self._add_new_match(progress)
        db.session.commit()
        return progress

    #Sets up debugging for canvasapi.
    def _setup_canvasapi_debugging(self):
        canvasapi_logger = logging.getLogger("canvasapi")
        canvasapi_handler = logging.StreamHandler(sys.stdout)
        canvasapi_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        canvasapi_handler.setLevel(logging.ERROR)
        canvasapi_handler.setFormatter(canvasapi_formatter)
        canvasapi_logger.addHandler(canvasapi_handler)
        canvasapi_logger.setLevel(logging.ERROR)

    #Returns a dict of student {login_id:id} corresponding to a canvas course object. Ex: {jsmith:13342}
    def _get_canvas_students(self):
        canvas_users = self._course.get_users()        
        canvas_students = {}
        # TODO: modify to only get active users
        for user in canvas_users:
            if hasattr(user, "login_id") and user.login_id is not None:
                canvas_students[user.login_id]=user.id  
        return canvas_students
    
    #Returns a dict of {id: {'posted_grade':score}} for all students in nb gradebook
    def _get_student_grades(self, canvas_students):
        with Gradebook("sqlite:////mnt/nbgrader/"+self._course_name+"/grader/gradebook.db") as gb:
        
            nb_assignment = gb.find_assignment(self._form_nb_assign_name)
            self._max_score = nb_assignment.max_score

            # TODO: can we change this to just get the students for this assignment? Investigate assignment.get_gradeable_students
            nb_students = gb.students            
            nb_grade_data = {}

            for nb_student in nb_students:

                nb_student_and_score = {}            

                # Try to find the submission in the nbgrader database. If it doesn't exist, the
                # MissingEntry exception will be raised and we assign them a score of None.
                try:
                    nb_submission = gb.find_submission(nb_assignment.name, nb_student.id)
                    nb_student_and_score['posted_grade'] = nb_submission.score
                except MissingEntry:
                    nb_student_and_score['posted_grade'] = None
                    

                # student.id will give us student's username, ie shrakibullah. we will need to compare this to
                # canvas's login_id instead of user_id

                # TEMP HACK: e7li and shrakibullah are instructors; change their ids (after 
                # submission fetch above) here to students in canvas course
                # TODO: create submissions for canvas course students
                # temp_nb_student_id = nb_student.id
                # if nb_student.id == 'e7li':
                #     temp_nb_student_id = 'testacct222'
                # if nb_student.id == 'shrakibullah':
                #     temp_nb_student_id = 'testacct333'                    

                # convert nbgrader username to canvas id (integer)
                canvas_student_id = canvas_students[nb_student.id]
                # canvas_student_id = canvas_students[temp_nb_student_id]
                nb_grade_data[canvas_student_id] = nb_student_and_score
            return nb_grade_data

    # gets existing canvas assignment
    def _get_assignment(self):
        app.logger.debug("upload submissions for existing canvas assignment;")
        assignment = self._course.get_assignment(self._form_canvas_assign_id)
        if assignment is None:
            raise Exception('Invalid form canvas_assign_id')
        return assignment

    def _get_max_score(self):
        with Gradebook("sqlite:////mnt/nbgrader/"+self._course_name+"/grader/gradebook.db") as gb:
            nb_assignment = gb.find_assignment(self._form_nb_assign_name)
            return nb_assignment.max_score

    # create new assignments as published
    def _create_assignment(self, max_score):
        app.logger.debug("upload submissions for non-existing canvas assignment; will be named: {}".format(self._form_nb_assign_name))             
        return self._course.create_assignment({'name':self._form_nb_assign_name, 'published':'true', 'assignment_group_id':self._group, 'points_possible':max_score})
        
    

    # Updates grades for given assignment. Returns progress resulting from upload attempt.
    def _submit_grades(self):
        progress = self.assignment_to_upload.submissions_bulk_update(grade_data=self.student_grades)
        try:
            session['progress_json'] = jsonpickle.encode(progress)
            session.modified = True
        except Exception:
            app.logger.debug("Error modifying session")
        app.logger.debug("progress url: {}".format(progress.url))
        time_out = time.time()+30
        while not progress.workflow_state == "completed" and not progress.workflow_state == "failed" and time_out > time.time():
            time.sleep(.1)
            progress = progress.query()
        return progress

    # Update existing match in database
    def _update_match(self, assignment_match, progress):
        app.logger.debug("Updating assignment in database")
        assignment_match.progress_url = progress.url
        assignment_match.last_updated_time = progress.updated_at
    
    # Creates and adds new match to database
    def _add_new_match(self, progress):
        app.logger.debug("Creating new assignment in database")
        newMatch = AssignmentMatch(course_id=self._course_id, nbgrader_assign_name=self._form_nb_assign_name,
                    canvas_assign_id=self.canvas_assignment_id, upload_progress_url=progress.url, last_updated_time=progress.updated_at)
        db.session.add(newMatch)