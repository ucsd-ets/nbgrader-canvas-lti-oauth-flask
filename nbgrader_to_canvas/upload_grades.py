from flask import Blueprint, session, request
from pylti.flask import lti

from .utils import error, redirect_open_circuit
from nbgrader_to_canvas import app, db, settings
from nbgrader.api import Gradebook, MissingEntry
from .models import AssignmentStatus
from .canvas import CanvasWrapper

import json
import logging
import sys

import sys
import time
#  Import the Canvas class
from canvasapi.assignment import (
    Assignment,
    AssignmentGroup,
    AssignmentOverride,
    AssignmentExtension,
)
from circuitbreaker import circuit


upload_grades_blueprint = Blueprint('upload_grades', __name__)
current_uploads = []  

# Web Views / Routes

@app.route('/remove_upload', methods=['POST'])
@circuit(failure_threshold=1, fallback_function=redirect_open_circuit)
def remove_upload():
    assignment = request.form.get('form_nb_assign_name')
    id = request.form.get('course_id')
    
    # raise Exception('remove_exception')
    status = AssignmentStatus.query.filter_by(nbgrader_assign_name=assignment, course_id=int(id)).first()
    out = ""
    if status:
        db.session.delete(status)
        out+="Status removed."
        db.session.commit()
    return out   

@app.route('/get_late_penalty', methods=['GET', 'POST'])
@circuit(failure_threshold=1, fallback_function=redirect_open_circuit)
def get_late_penalty():
    assignment = request.form.get('assignment')
    id = request.form.get('course_id')

    # raise Exception('late_penalty exception')
    status = AssignmentStatus.query.filter_by(nbgrader_assign_name=assignment, course_id=int(id)).first()
    if status:
        return str(status.late_penalty)
    return '0'
   

@app.route('/get_progress', methods=['GET'])
@circuit(failure_threshold=10, fallback_function=redirect_open_circuit)
def get_progress():
    """
    Endpoint to call from JS. queries the database for a specified assignment and returns the upload
    url for the assignment as a JSON.

    If no status is in the database, it returns null to JS.
    """
    assignment = request.args.get('assignment')
    id = request.args.get('course_id')
    # raise Exception('get_progress_exception')
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
def upload_grades(course_name="TEST_NBGRADER", lti=lti):
    if not request.method == "POST":
        return None

    course_id = request.form.get('course_id')
    group = request.form.get('group')
    form_canvas_assign_id = request.form.get('form_canvas_assign_id') 
    form_nb_assign_name = request.form.get('form_nb_assign_name')
    late_penalty = request.form.get('late_penalty')

    
    reset_status(form_nb_assign_name, course_id)
    upload(course_id, group, form_canvas_assign_id, form_nb_assign_name, course_name, late_penalty, lti)
    return "upload complete"
    
def reset_status(form_nb_assign_name, course_id):
    # raise Exception('reset_exception')
    status = AssignmentStatus.query.filter_by(nbgrader_assign_name=form_nb_assign_name, course_id=int(course_id)).first()
    if status:
        status.completion=0
        status.status='Initializing'
        db.session.commit()

def upload(course_id, group, form_canvas_assign_id, form_nb_assign_name, course_name, late_penalty, lti):
    try:
        
        uploader = UploadGrades(course_id, group, form_canvas_assign_id, form_nb_assign_name, course_name, late_penalty, lti)
        global current_uploads
        current_uploads.append(form_nb_assign_name)
        uploader.init_course()
        #raise Exception('upload_exception')
        uploader.parse_form_data()
        uploader.update_database()
        current_uploads.remove(form_nb_assign_name)
    except Exception as ex:
        try:
            status = AssignmentStatus.query.filter_by(nbgrader_assign_name=form_nb_assign_name, course_id=int(course_id)).first()
            if status:
                status.completion=0
                status.status='Failed'
                db.session.commit()
        except Exception as exc:
            pass
        current_uploads.remove(form_nb_assign_name)
        raise ex

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
    
    def init_course(self, flask_session = session):
        self._setup_status()
        canvas_wrapper = CanvasWrapper(settings.API_URL, flask_session)
        canvas = canvas_wrapper.get_canvas()
        self._course = canvas.get_course(self._course_id)
        if self._course is None:
            raise Exception('Invalid course id')
            
    def parse_form_data(self):
        if (self._form_canvas_assign_id == 'create'):
            max_score = self._get_max_score()
            self.assignment_to_upload = self._create_assignment(max_score)
            self.assignment_status.canvas_assign_id = self.assignment_to_upload.id
            db.session.commit()
        else: 
            self.assignment_to_upload = self._get_assignment()

        canvas_students = self._get_canvas_students()
        self.student_grades = self._get_student_grades(canvas_students)
        self.canvas_assignment_id = self.assignment_to_upload.id
        
    def update_database(self):
        progress = self._submit_grades()
        
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
                    self.assignment_status.completion = 10*counter/self._num_students
                    db.session.commit()
        return canvas_students
    
    def _get_student_grades(self, canvas_students):
        '''Returns a dict of {id: {'posted_grade':score}} for all students in nb gradebook'''
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

    def _get_assignment(self):
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
        return self._course.create_assignment({'name':self._form_nb_assign_name, 'published':'true', 'assignment_group_id':self._group, 'points_possible':max_score})
        
    

    # Updates grades for given assignment. Returns progress resulting from upload attempt.
    def _submit_grades(self):
        self.assignment_status.status = 'Uploading Grades'
        db.session.commit()
        self.assignment_to_upload.edit(assignment={'published':True})
        progress = self.assignment_to_upload.submissions_bulk_update(grade_data=self.student_grades)
        counter = 0
        while not progress.workflow_state == "completed" and not progress.workflow_state == "failed":
            time.sleep(1)
            # The status bar progression is based on the assumption of linear time with 323 students taking around 75 seconds
            # Uploads don't happen asynchronously, so this becomes very innacurrate if multiple uploads are taking place
            counter +=1
            if self.assignment_status.completion < 95:
                self.assignment_status.completion = 55 + 35*counter*4/self._num_students
                db.session.commit()
            progress = progress.query()
        return progress

    def _update_status(self, progress):
        self.assignment_status.upload_progress_url = progress.url
        db.session.commit()
