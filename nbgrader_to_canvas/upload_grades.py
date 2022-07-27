from flask import Blueprint, session, request
from pylti.flask import lti

from .utils import error, redirect_open_circuit, open_gradebook
from nbgrader_to_canvas import app, db, settings
from nbgrader.api import Gradebook, MissingEntry
from .models import AssignmentStatus
from .canvas import CanvasWrapper
from . import settings

import json
import logging
import sys
import requests

import sys
import time
import os
from os import path
#  Import the Canvas class
from canvasapi.assignment import (
    Assignment,
    AssignmentGroup,
    AssignmentOverride,
    AssignmentExtension,
)
from circuitbreaker import circuit


upload_grades_blueprint = Blueprint('upload_grades', __name__)
remove_upload_blueprint = Blueprint('remove_upload', __name__)
get_late_penalty_blueprint = Blueprint('get_late_penalty', __name__)
get_progress_blueprint = Blueprint('get_progress', __name__)
current_uploads = []  

# Web Views / Routes

@remove_upload_blueprint.route('/remove_upload', methods=['GET', 'POST'])
@circuit(failure_threshold=1, fallback_function=redirect_open_circuit)
def remove_upload():
    assignment = request.form.get('form_nb_assign_name')
    id = request.form.get('course_id')
    
    status = AssignmentStatus.query.filter_by(nbgrader_assign_name=assignment, course_id=int(id)).first()
    out = ""
    if status:
        db.session.delete(status)
        out+="Status removed."
        db.session.commit()
    return out   

@get_late_penalty_blueprint.route('/get_late_penalty', methods=['GET', 'POST'])
@circuit(failure_threshold=1, fallback_function=redirect_open_circuit)
def get_late_penalty():
    assignment = request.form.get('assignment')
    id = request.form.get('course_id')

    status = AssignmentStatus.query.filter_by(nbgrader_assign_name=assignment, course_id=int(id)).first()
    if status:
        return str(status.late_penalty)
    return '0'
   

@get_progress_blueprint.route('/get_progress', methods=['GET'])
@circuit(failure_threshold=10, fallback_function=redirect_open_circuit)
def get_progress():
    """
    Endpoint to call from JS. queries the database for a specified assignment and returns the upload
    url for the assignment as a JSON.

    If no status is in the database, it returns null to JS.
    """
    assignment = request.args.get('assignment')
    id = request.args.get('course_id')
    
    status = AssignmentStatus.query.filter_by(nbgrader_assign_name=assignment, course_id=int(id)).first()
    if status:
        if status.status == 'Uploaded':
            return json.dumps({'status': status.status, 'completion': status.completion, 'canvas_assign_id': status.canvas_assign_id})
        return json.dumps({'status': status.status, 'completion': status.completion})
    else:
        return json.dumps(status)


@upload_grades_blueprint.route('/upload_grades', methods=['GET', 'POST'])
@circuit(failure_threshold=1, fallback_function=redirect_open_circuit)
@lti(error=error, request='session', role='staff', app=app)
def upload_grades(lti=lti):
    if not request.method == "POST":
        return None

    course_id = request.form.get('course_id')
    group = request.form.get('group')
    form_canvas_assign_id = request.form.get('form_canvas_assign_id') 
    form_nb_assign_name = request.form.get('form_nb_assign_name')
    late_penalty = request.form.get('late_penalty')
    feedback_checkbox = request.form.get('feedback_checkbox')

    update_status(form_nb_assign_name, course_id,completion=0,status='Initializing')
    upload(course_id, group, form_canvas_assign_id, form_nb_assign_name, late_penalty, feedback_checkbox, lti)
    return "upload complete"

def upload(course_id, group, form_canvas_assign_id, form_nb_assign_name, late_penalty, feedback_checkbox, lti):
    global current_uploads
    try:
        uploader = UploadGrades(course_id, group, form_canvas_assign_id, form_nb_assign_name, late_penalty, feedback_checkbox, lti)
        current_uploads.append(form_nb_assign_name)
        uploader.init_course()
        uploader.parse_form_data()
        uploader.update_database()
        current_uploads.remove(form_nb_assign_name)
    except Exception as ex:
        current_uploads.remove(form_nb_assign_name)
        try:
            update_status(form_nb_assign_name,course_id,completion=0,status='Failed')
        except Exception as exc:
            pass
        raise ex

def update_status(nbgrader_assign_name, course_id, canvas_assign_id=None, status=None, completion=None, late_penalty=None,upload_progress_url=None):
    db_status=AssignmentStatus.query.filter_by(nbgrader_assign_name=nbgrader_assign_name, course_id=int(course_id)).first()
    if db_status:
        if canvas_assign_id:
            db_status.canvas_assign_id = canvas_assign_id
        if status:
            db_status.status = status
        if completion:
            db_status.completion = completion
        if late_penalty:
            db_status.late_penalty = late_penalty
        if upload_progress_url:
            db_status.upload_progress_url = upload_progress_url
        db.session.commit()

class UploadGrades:

    def __init__(self, course_id, group, form_canvas_assign_id, form_nb_assign_name, late_penalty, feedback_checkbox, lti=lti):
        self._course_id = course_id
        self._group = group
        self._form_canvas_assign_id = form_canvas_assign_id
        self._form_nb_assign_name = form_nb_assign_name
        self._late_penalty=late_penalty
        self._feedback_checkbox=feedback_checkbox
        self._lti = lti
        self.nbgrader_feedback = {}
        self._setup_canvasapi_debugging()
    
    def init_course(self, flask_session = session, testing=False):
        self._flask_session = flask_session

        canvas_wrapper = CanvasWrapper(settings.API_URL, flask_session)
        self._course = canvas_wrapper.get_canvas().get_course(self._course_id)
        if self._course is None:
            raise Exception('Invalid course id')

        self._setup_status()
        self._setup_gradebook_path(testing)
        self._num_students = self._get_num_students(gb=self._nbgrader_course)

        
    

    def parse_form_data(self):
        if (self._form_canvas_assign_id == 'create'):
            max_score = self._get_max_score(gb=self._nbgrader_course)
            self.assignment_to_upload = self._create_assignment(max_score)
            update_status(self._form_nb_assign_name, self._course_id, canvas_assign_id=self.assignment_to_upload.id)
        else: 
            self.assignment_to_upload = self._get_assignment()

        self.canvas_students = self._get_canvas_students()
        if(self._feedback_checkbox == "true"):
            self._delete_comments(gb=self._nbgrader_course)        
            self._get_feedbacks(gb=self._nbgrader_course)
        self.student_grades = self._get_student_grades(gb=self._nbgrader_course)
        self.canvas_assignment_id = self.assignment_to_upload.id
        
    def update_database(self):
        progress = self._submit_grades()
        update_status(self._form_nb_assign_name, self._course_id, status='Uploaded', completion=100,upload_progress_url=progress.url)
        return progress

    def _setup_status(self):
        self.assignment_status = AssignmentStatus.query.filter_by(course_id = self._course_id, nbgrader_assign_name = self._form_nb_assign_name).first()
        if self.assignment_status:
            update_status(self._form_nb_assign_name, self._course_id, status='Initializing', completion=0, late_penalty=self._late_penalty)
        else:
            self._create_assignment_status()

    def _setup_gradebook_path(self, testing):
        if testing or self._course.course_code == 'ET-MCC-CCET_FA20':
            self._nbgrader_course = 'TEST_NBGRADER'
        else:
            self._nbgrader_course = self._course.course_code
        if not path.exists("/mnt/nbgrader/"+self._nbgrader_course+"/grader/gradebook.db"):
            print("Gradebook missing for: {}".format(self._nbgrader_course))
            raise Exception("Gradebook missing for: {}".format(self._nbgrader_course))

    def _create_assignment_status(self):
        self.assignment_status = AssignmentStatus(course_id=self._course_id, nbgrader_assign_name=self._form_nb_assign_name , canvas_assign_id=self._form_canvas_assign_id, status = 'Initializing', completion = 0, late_penalty=self._late_penalty)
        db.session.add(self.assignment_status)
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

    def _get_canvas_students(self):
        '''Returns a dict of student {login_id:id} corresponding to a canvas course object. Ex: {jsmith:13342}
        The counter on this is only accurate if num_students is the number of students in the class
        '''
        self.assignment_status.status = 'Fetching Students'
        canvas_students = {}
        canvas_users = self._course.get_users()  
        counter=0
        for user in canvas_users:
            if hasattr(user, "login_id") and user.login_id is not None:
                canvas_students[user.login_id]=user.id  
                if counter < self._num_students:
                    counter += 1
                    update_status(self._form_nb_assign_name, self._course_id, completion=5*counter/self._num_students)
        return canvas_students
    
    @open_gradebook
    def _get_nb_students(self, gb, canvas_students):
        raw_students = gb.students
        nb_students = []
        for student in raw_students:
            if(student.id in canvas_students.keys()):
                nb_students.append(student)
        return nb_students
    
    @open_gradebook
    def _get_student_grades(self, gb):
        '''Returns a dict of {id: {'posted_grade':score}} for all students in nb gradebook'''
        update_status(self._form_nb_assign_name, self._course_id, status='Fetching Grades')
        nb_assignment = gb.find_assignment(self._form_nb_assign_name)
        
        nb_students = self._get_nb_students(gb=self._nbgrader_course, canvas_students=self.canvas_students)     
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

                # if nb_student.id in self.nbgrader_feedback:
                #     nb_student_and_score['file_ids'] = [self.nbgrader_feedback[nb_student.id]]
                #     nb_student_and_score['text_comment'] = 'Transferred from datahub.'

            except MissingEntry:
                nb_student_and_score['posted_grade'] = ''


            # student.id will give us student's username, ie shrakibullah. we will need to compare this to
            # canvas's login_id instead of user_id              

            # convert nbgrader username to canvas id (integer)
            canvas_student_id = self.canvas_students[nb_student.id]
            nb_grade_data[canvas_student_id] = nb_student_and_score
            counter += 1
            update_status(self._form_nb_assign_name, self._course_id, completion=35+30*counter/self._num_students)
        return nb_grade_data

    def _get_assignment(self):
        assignment = self._course.get_assignment(self._form_canvas_assign_id)
        if assignment is None:
            raise Exception(f'Invalid form canvas_assign_id: {self._form_canvas_assign_id}')
        return assignment

    @open_gradebook
    def _get_max_score(self,gb):
        nb_assignment = gb.find_assignment(self._form_nb_assign_name)
        return nb_assignment.max_score

    @open_gradebook
    def _get_num_students(self,gb):
        return len(gb.students)

    def _create_assignment(self, max_score):
        return self._course.create_assignment({'name':self._form_nb_assign_name, 'published':'true', 'assignment_group_id':self._group, 'points_possible':max_score})
        
    @open_gradebook
    def _delete_comments(self,gb):
        '''clears old comments from submission to prevent cluttering of the comment section in case of re-submission'''
        update_status(self._form_nb_assign_name, self._course_id, completion=5, status='Removing Old Feedback')
        counter = 0
        nb_students = self._get_nb_students(gb=self._nbgrader_course, canvas_students=self.canvas_students)
        for student in nb_students:
            submission = self.assignment_to_upload.get_submission(self.canvas_students[student.id],include=['submission_comments'])
            
            for comment in submission.submission_comments:
                if comment.comment == 'See attached files.':
                    try:
                        submission.delete_comment(comment.id)
                    except AttributeError as ae:
                        pass

            if counter < self._num_students:
                counter += 1
                update_status(self._form_nb_assign_name, self._course_id, completion=5+15*counter/self._num_students)
            
    @open_gradebook
    def _get_feedbacks(self,gb):
        update_status(self._form_nb_assign_name, self._course_id, completion=20, status='Fetching Feedback')
        counter = 0
        nb_students = self._get_nb_students(gb=self._nbgrader_course, canvas_students=self.canvas_students)
        for student in nb_students:
            submission = self.assignment_to_upload.get_submission(self.canvas_students[student.id],include=['submission_comments'])
            student_feedback_dir = f'/mnt/nbgrader/{self._nbgrader_course}/grader/feedback/{student.id}/{self._form_nb_assign_name}'
            if not os.path.isdir(student_feedback_dir):
                continue

            for file in os.listdir(student_feedback_dir):
                if file.endswith('.html'):
                    response = submission.upload_comment(f'{student_feedback_dir}/{file}')
                    if not response[0]:
                        app.logger.debug('Comment Upload Failed')
                    self.nbgrader_feedback[student.id] = response[1]['id']
            if counter < self._num_students:
                counter += 1
                update_status(self._form_nb_assign_name, self._course_id, completion=20+15*counter/self._num_students)

    # Updates grades for given assignment. Returns progress resulting from upload attempt.
    # Progress object includes status information (queued,running,completed,failed). It also contains
    # completion(0-100), but that functionality does not currently work for bulk update.
    def _submit_grades(self):
        update_status(self._form_nb_assign_name, self._course_id, status='Uploading Grades')
        self.assignment_to_upload.edit(assignment={'published':True})
        progress = self.assignment_to_upload.submissions_bulk_update(grade_data=self.student_grades)
        counter = 0
        while not progress.workflow_state == "completed" and not progress.workflow_state == "failed":
            time.sleep(1)
            # The status bar progression is based on the assumption of linear time with 323 students taking around 75 seconds
            # Uploads don't happen asynchronously, so this becomes very innacurrate if multiple uploads are taking place
            counter +=1
            if self.assignment_status.completion < 95:
                update_status(self._form_nb_assign_name, self._course_id, completion=65 + 30*counter*4/self._num_students)
            else:
                update_status(self._form_nb_assign_name, self._course_id, completion=95)
            progress = progress.query()
        return progress
