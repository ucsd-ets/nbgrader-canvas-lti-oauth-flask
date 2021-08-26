from types import GetSetDescriptorType
from typing import Counter
from flask import Blueprint, render_template, session, request, redirect, url_for
from flask_session import Session
from pybreaker import CircuitBreakerError
from pylti.flask import lti

from .utils import error
from nbgrader_to_canvas import app, db, db_breaker, settings
from nbgrader.api import Gradebook, MissingEntry
from .models import AssignmentStatus
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
import asyncio
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

from nbgrader_to_canvas import canvas

upload_grades_blueprint = Blueprint('upload_grades', __name__)

# Web Views / Routes

@app.route('/remove_upload', methods=['POST'])
def remove_upload():
    assignment = request.form.get('form_nb_assign_name')
    id = request.form.get('course_id')
    try:
        status = AssignmentStatus.query.filter_by(nbgrader_assign_name=assignment, course_id=int(id)).first()
        out = ""
        if status:
            db.session.delete(status)
            out+="Status removed."
        db.session.commit()
        return out
    except Exception as ex:
        app.logger.debug(ex)    

@app.route('/get_late_penalty', methods=['GET', 'POST'])
def get_late_penalty():
    assignment = request.form.get('assignment')
    id = request.form.get('course_id')
    try:
        status = AssignmentStatus.query.filter_by(nbgrader_assign_name=assignment, course_id=int(id)).first()
        if status:
            return str(status.late_penalty)
        return '0'
    except Exception as ex:
        app.logger.debug(ex)
        return '-'
   

@app.route('/get_progress', methods=['GET'])
def get_progress():

    """
    Endpoint to call from JS. queries the database for a specified assignment and returns the upload
    url for the assignment as a JSON.

    If no status is in the database, it returns null to JS.
    """

    # get assignment and course for db query
    assignment = request.args.get('assignment')
    id = request.args.get('course_id')
    
    try:
        status = AssignmentStatus.query.filter_by(nbgrader_assign_name=assignment, course_id=int(id)).first()

        # if match found, return db upload url as a json
        if status:
            #app.logger.debug("found match: {}, {}, {}".format(match.canvas_assign_id, assignment, id))
            #app.logger.debug("{}".format(requests.get(match.upload_progress_url).json()))
            if status.status == 'Uploaded':
                return json.dumps({'status': status.status, 'completion': status.completion, 'canvas_assign_id': status.canvas_assign_id})
            return json.dumps({'status': status.status, 'completion': status.completion})

        # if match not found, return null
        else:
            return json.dumps(status)
    except Exception as ex:
        app.logger.debug(ex)
        return json.dumps({'error' : str(ex)})  


@upload_grades_blueprint.route('/upload_grades', methods=['GET', 'POST'])
@lti(error=error, request='session', role='staff', app=app)
def upload_grades(course_name="TEST_NBGRADER", lti=lti):
    #If not posting, don't upload anything
    if not request.method == "POST":
        return None

    course_id = request.form.get('course_id')
    group = request.form.get('group')
    form_canvas_assign_id = request.form.get('form_canvas_assign_id') 
    form_nb_assign_name = request.form.get('form_nb_assign_name')
    late_penalty = request.form.get('late_penalty')

    try:
        try:
            status = AssignmentStatus.query.filter_by(nbgrader_assign_name=form_nb_assign_name, course_id=int(course_id)).first()
            if status:
                status.completion=0
                status.status='Initializing'
                db.session.commit()
                app.logger.debug("status updated")
        except Exception as ex:
            app.logger.debug(ex)
        uploader = UploadGrades(course_id, group, form_canvas_assign_id, form_nb_assign_name, course_name, late_penalty, lti)
        global current_uploads
        current_uploads.append(form_nb_assign_name)
        threaded_upload(uploader)
    except Exception as ex:
        return "upload failed"
    return "upload complete"

current_uploads = []    

def threaded_upload(uploader):
    global current_uploads
    try:
        uploader.init_course()
        uploader.parse_form_data()
        uploader.update_database()
        current_uploads.remove(uploader._form_nb_assign_name)
    except Exception as ex:
        app.logger.error("Upload Failed:")
        try:
            status = AssignmentStatus.query.filter_by(nbgrader_assign_name=uploader._form_nb_assign_name).first()
            status.status = 'Failed'
            status.completion = 0
            db.session.commit()
        except Exception as exc:
            app.logger.debug("Error failing upload: ")
        current_uploads.remove(uploader._form_nb_assign_name)
        raise Exception("Upload Failed")
    
    
    

class UploadGrades:

    def __init__(self, course_id, group, form_canvas_assign_id, form_nb_assign_name, course_name, late_penalty, lti=lti):
       
        self._course_id = course_id
        self._group = group
        self._form_canvas_assign_id = form_canvas_assign_id
        self._form_nb_assign_name = form_nb_assign_name
        self._course_name = course_name
        self._late_penalty=late_penalty
        self._lti = lti
        self._setup_canvasapi_debugging()
        self._num_students = self._get_num_students()
        

    # Returns a course object corresponding to given course_id
    # TEST: param is to allow testing
    def init_course(self, flask_session = session):
        self._setup_status()
        canvas_wrapper = CanvasWrapper(settings.API_URL, flask_session)
        canvas = canvas_wrapper.get_canvas()
        self._course = canvas.get_course(self._course_id)
        if self._course is None:
            raise Exception('Invalid course id')
    
    def parse_form_data(self):
        if (self._form_canvas_assign_id == 'create'):
            app.logger.debug('get max score')
            max_score = self._get_max_score()
            app.logger.debug('create assignment')
            self.assignment_to_upload = self._create_assignment(max_score)
            self.assignment_status.canvas_assign_id = self.assignment_to_upload.id
            db.session.commit()
        else: 
            self.assignment_to_upload = self._get_assignment()

        app.logger.debug('get canvas students')
        time_start = time.time()
        canvas_students = self._get_canvas_students()
        app.logger.debug('time for get students: {}'.format(time.time()-time_start))
        app.logger.debug('get student grades')
        time_start = time.time()
        self.student_grades = self._get_student_grades(canvas_students)
        app.logger.debug('time for get grades: {}'.format(time.time()-time_start))

        self.canvas_assignment_id = self.assignment_to_upload.id
        
    
    # Submits grades to canvas, and creates/updates the progress for AssignmentStatus database for the assignment
    def update_database(self):
        app.logger.debug('submit grades')
        time_start = time.time()
        progress = self._submit_grades()
        app.logger.debug('time for submit: {}'.format(time.time()-time_start))
        
        self._update_status(progress)
        self.assignment_status.status = 'Uploaded'
        self.assignment_status.completion = 100
        db.session.commit()
        return progress

    def _setup_status(self):
        self.assignment_status = AssignmentStatus.query.filter_by(course_id = self._course_id, nbgrader_assign_name = self._form_nb_assign_name).first()
        if self.assignment_status:
            self._refresh_assignment_status()
        else:
            self._create_assignment_status()

    def _create_assignment_status(self):
        self.assignment_status = AssignmentStatus(course_id=self._course_id, nbgrader_assign_name=self._form_nb_assign_name , canvas_assign_id=self._form_canvas_assign_id, status = 'Initializing', completion = 0, late_penalty=self._late_penalty)
        db.session.add(self.assignment_status)
        db.session.commit()

    def _refresh_assignment_status(self):
        self.assignment_status.status = 'Initializing'
        self.assignment_status.completion = 0
        self.assignment_status.late_penalty=self._late_penalty
        db.session.commit()

    #Sets up debugging for canvasapi
    def _setup_canvasapi_debugging(self):
        canvasapi_logger = logging.getLogger("canvasapi")
        canvasapi_handler = logging.StreamHandler(sys.stdout)
        canvasapi_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        canvasapi_handler.setLevel(logging.ERROR)
        canvasapi_handler.setFormatter(canvasapi_formatter)
        canvasapi_logger.addHandler(canvasapi_handler)
        canvasapi_logger.setLevel(logging.ERROR)

    #Returns a dict of student {login_id:id} corresponding to a canvas course object. Ex: {jsmith:13342}
    # The counter on this is only accurate if num_students is the number of students in the class
    def _get_canvas_students(self):
        self.assignment_status.status = 'Fetching Students'
        canvas_students = {}
        canvas_users = self._course.get_users()  
        counter=0
        for user in canvas_users:
            if hasattr(user, "login_id") and user.login_id is not None:
                canvas_students[user.login_id]=user.id  
                if counter < self._num_students:
                    counter += 1
                    self.assignment_status.completion = 10*counter/self._num_students
                    db.session.commit()
        return canvas_students
    
    #Returns a dict of {id: {'posted_grade':score}} for all students in nb gradebook
    def _get_student_grades(self, canvas_students):
        self.assignment_status.status = 'Fetching Grades'
        db.session.commit()
        with Gradebook("sqlite:////mnt/nbgrader/"+self._course_name+"/grader/gradebook.db") as gb:
            nb_assignment = gb.find_assignment(self._form_nb_assign_name)
            
            nb_students = gb.students            
            nb_grade_data = {}

            counter = 0            
            for nb_student in nb_students:

                nb_student_and_score = {} 
                      

                # Try to find the submission in the nbgrader database. If it doesn't exist, the
                # MissingEntry exception will be raised and we assign them a score of None.
                
                try:
                    
                    nb_submission = gb.find_submission(nb_assignment.name, nb_student.id)
                    if nb_submission.total_seconds_late > 0:
                        nb_student_and_score['posted_grade'] = nb_submission.score*(100-int(self._late_penalty))/100
                    else:
                        nb_student_and_score['posted_grade'] = nb_submission.score
                except MissingEntry:
                    nb_student_and_score['posted_grade'] = ''

                
                    

                # student.id will give us student's username, ie shrakibullah. we will need to compare this to
                # canvas's login_id instead of user_id              

                # convert nbgrader username to canvas id (integer)
                canvas_student_id = canvas_students[nb_student.id]
                nb_grade_data[canvas_student_id] = nb_student_and_score
                counter += 1
                self.assignment_status.completion = 10+45*counter/self._num_students
                db.session.commit()
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

    def _get_num_students(self):
        with Gradebook("sqlite:////mnt/nbgrader/"+self._course_name+"/grader/gradebook.db") as gb:
            return len(gb.students)

    # create new assignments as published
    def _create_assignment(self, max_score):
        app.logger.debug("upload submissions for non-existing canvas assignment; will be named: {}".format(self._form_nb_assign_name))             
        return self._course.create_assignment({'name':self._form_nb_assign_name, 'published':'true', 'assignment_group_id':self._group, 'points_possible':max_score})
        
    

    # Updates grades for given assignment. Returns progress resulting from upload attempt.
    def _submit_grades(self):
        self.assignment_status.status = 'Uploading Grades'
        app.logger.debug(self.assignment_to_upload)
        db.session.commit()
        self.assignment_to_upload.edit(assignment={'published':True})
        app.logger.debug(self.assignment_to_upload.published)
        progress = self.assignment_to_upload.submissions_bulk_update(grade_data=self.student_grades)

        app.logger.debug("progress url: {}".format(progress.url))
        counter = 0
        while not progress.workflow_state == "completed" and not progress.workflow_state == "failed":
            time.sleep(1)
            # The status bar progression is based on the assumption of linear time with 323 students taking around 75 seconds
            counter +=1
            if self.assignment_status.completion < 95:
                self.assignment_status.completion = 55 + 35*counter*4/self._num_students
                db.session.commit()
            progress = progress.query()
        return progress

    # Add/update progress url in database
    def _update_status(self, progress):
        app.logger.debug("Updating assignment in database")
        self.assignment_status.upload_progress_url = progress.url
        db.session.commit()
