from nbgrader_to_canvas.upload_grades import UploadGrades
from nbgrader_to_canvas.models import AssignmentMatch, Users
from canvasapi import Canvas
from flask import session
from . import canvas_students, student_grades, existing_assignment
import unittest
import pytest
from nbgrader_to_canvas import db, app

import time

class TestUploadGrades(unittest.TestCase):
    @pytest.fixture(autouse = True)
    def user(self):
        self._user = Users(114217,'13171~qKHvThhYQrIr0HfTicEEfmBD1DeLG7YM7FZD4RMtf5iFfoyr1eFPKy7lR8kWxJWT',10)
        db.session.add(self._user)
        db.session.commit()
        yield self._user
        db.session.delete(self._user)
        db.session.commit()
    
    @pytest.fixture(autouse = True)
    def uploader(self, user):
        self.uploader = UploadGrades(20774, 92059, 326429, 'Test Assignment 2')

    def test_init_course(self):
        self.uploader.init_course({'canvas_user_id': '114217'})
        assert str(self.uploader._course) == 'ET-MCC-CCET_FA20 Canvas Caliper Events Testing (20774)'

    def test_get_canvas_students(self):
        self.uploader.init_course({'canvas_user_id': '114217'})
        students = self.uploader._get_canvas_students()
        assert students == canvas_students    

    def test_get_student_grades(self):
        grades = self.uploader._get_student_grades(canvas_students)
        assert grades == student_grades
    
    def test_get_assignment(self):
        self.uploader.init_course({'canvas_user_id': '114217'})
        assignment = self.uploader._get_assignment()
        assert assignment.name == existing_assignment
    
    def test_create_assignment(self):
        customUploader = UploadGrades(20774, 92059, 'create', 'Test Assignment 3')
        customUploader.init_course({'canvas_user_id': '114217'})
        assignment = customUploader._create_assignment()
        assert assignment.name == 'Test Assignment 3'
        assignment.delete()


    def test_submit_grades(self):
        self.uploader.init_course({'canvas_user_id': '114217'})
        self.uploader.parse_form_data()
        progress = self.uploader._submit_grades()   
        time_out = time.time()+80
        while not progress.workflow_state == 'completed' and not progress.workflow_state == 'failed':
            time.sleep(.1)
            progress = progress.query()
            if time.time() > time_out:
                print("_submit_grades timed out")
                print(progress.completion)
                assert False
        assert progress.workflow_state == 'completed'

    def test_update_match(self):
        self.uploader.init_course({'canvas_user_id': '114217'})
        self.uploader.parse_form_data()
        progress = self.uploader._submit_grades()
        assignment_match = AssignmentMatch.query.filter_by(nbgrader_assign_name=self.uploader._form_nb_assign_name, course_id=self.uploader._course_id).first()
        self.uploader._update_match(assignment_match, progress)
        db.session.commit()
        match = AssignmentMatch.query.filter_by(nbgrader_assign_name=self.uploader._form_nb_assign_name, course_id=self.uploader._course_id).first()
        assert match.progress_url == progress.url

    #TODO: add a cleanup that deletes everything even if test fails
    def test_add_new_match(self):
        customUploader = UploadGrades(20774, 92059, 'create', 'Test Assignment 3')
        customUploader.init_course({'canvas_user_id': '114217'})
        customUploader.parse_form_data()
        progress = customUploader._submit_grades()
        before = AssignmentMatch.query.filter_by(nbgrader_assign_name=customUploader._form_nb_assign_name, course_id=customUploader._course_id).first()
        customUploader._add_new_match(progress)
        after = AssignmentMatch.query.filter_by(nbgrader_assign_name=customUploader._form_nb_assign_name, course_id=customUploader._course_id).first()
        assert not before == after
        db.session.delete(after)
        db.session.commit()
        customUploader.assignment_to_upload.delete()

    