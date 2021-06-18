from nbgrader_to_canvas.upload_grades import UploadGrades
from nbgrader_to_canvas.models import Users
from canvasapi import Canvas
from flask import session
from . import canvas_students, student_grades, existing_assignment
import unittest
import pytest
from nbgrader_to_canvas import db, app

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
        # TODO: Find a way to test without relying on init_course
        self.uploader.init_course({'canvas_user_id': '114217'})
        assignment = self.uploader._get_assignment()
        assert str(assignment) == existing_assignment
    
    def test_create_assignment(self):
        customUploader = UploadGrades(20774, 92059, 'create', 'Created Assignment 1')
        customUploader.init_course({'canvas_user_id': '114217'})
        assignment = customUploader._create_assignment()
        assert False

    def test_submit_assignment(self):
        assert False

    def test_update_matches(self):
        assert False

    