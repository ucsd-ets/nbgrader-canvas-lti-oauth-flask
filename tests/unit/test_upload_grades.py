from nbgrader_to_canvas.upload_grades import UploadGrades
from nbgrader_to_canvas.models import AssignmentMatch, Users
from canvasapi import Canvas
from flask import session
from tests.unit import canvas_students, student_grades, existing_assignment
import unittest
import pytest
from nbgrader_to_canvas import db, app

import time

class TestUploadGrades(unittest.TestCase):
    @pytest.fixture(autouse = True)
    def user(self):
        self._user = Users(114217,'13171~bngbhxjVx3G7sqnWFC3BFs0r9MgN408enlV3I3uN74pCPpjkQvK2bI3eEcStdPH1',10)
        db.session.add(self._user)
        db.session.commit()
        yield self._user
        db.session.delete(self._user)
        db.session.commit()
    
    @pytest.fixture(autouse = True)
    def uploader(self, user):
        self.uploader = UploadGrades(20774, 92059, 337353, 'Test Assignment 2')

    def test_init_course_returns_course_for_valid_course_id(self):
        self.uploader.init_course({'canvas_user_id': '114217'})
        assert self.uploader._course.name == 'Canvas Caliper Events Testing'
    
    def test_init_course_raises_error_for_invalid_course_id(self):
        self.uploader._course_id=1234
        try:
            self.uploader.init_course({'canvas_user_id': '114217'})
        except Exception as e:
            return
        assert False

    def test_get_canvas_students(self):
        self.uploader.init_course({'canvas_user_id': '114217'})
        students = self.uploader._get_canvas_students()
        print(students)
        assert students == canvas_students    

    def test_get_student_grades_returns_grades_for_valid_course_name(self):
        grades = self.uploader._get_student_grades(canvas_students)
        assert grades == student_grades
    
    def test_get_student_grades_raises_error_for_invalid_course_name(self):
        self.uploader._course_name = 'invalid name'
        try:
            self.uploader._get_student_grades(canvas_students)
        except Exception as e:
            print("{}".format(e))
            return
        assert False
    
    def test_get_assignment_returns_assignment_for_valid_form_data(self):
        self.uploader.init_course({'canvas_user_id': '114217'})
        assignment = self.uploader._get_assignment()
        assert assignment.name == existing_assignment

    def test_get_assignment_raises_error_for_invalid_form_data(self):
        self.uploader.init_course({'canvas_user_id': '114217'})
        self.uploader._form_canvas_assign_id = 1234
        try:
            self.uploader._get_assignment()
        except Exception as e:
            print("{}".format(e))
            return
        assert False
    
    def test_create_assignment(self):
        try:
            assignments = self.uploader._course.get_assignments()
            for a in assignments:
                if a.name == 'Test Assignment 3':
                    match = AssignmentMatch.query.filter_by(nbgrader_assign_name=a.name, course_id=20774).first()
                    if match:
                        db.session.delete(match)
                    a.delete()
            db.session.commit()
        except Exception as e:
            print(e)
        custom_uploader = UploadGrades(20774, 92059, 'create', 'Test Assignment 3')
        custom_uploader.init_course({'canvas_user_id': '114217'})
        assignment = custom_uploader._create_assignment()
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

    # Checks the grade of Test Account 333, Test Assignment 1
    def test_grades_match(self):
        self.uploader.init_course({'canvas_user_id': '114217'})
        # TODO: Use canvas rest api to check if the uploaded grade matches what is expected from nbgrader.
        # Step 1: Remove assignment from canvas
        try:
            assignments = self.uploader._course.get_assignments()
            for a in assignments:
                if a.name == 'Test Assignment 1':
                    print('here')
                    match = AssignmentMatch.query.filter_by(nbgrader_assign_name=a.name, course_id=20774).first()
                    if match:
                        db.session.delete(match)
                    a.delete()
            db.session.commit()
        except Exception as e:
            print(e)
        # Step 2: Call upload grades
        custom_uploader = UploadGrades(20774, 92059, 'create', 'Test Assignment 1')
        custom_uploader.init_course({'canvas_user_id': '114217'})
        custom_uploader.parse_form_data()
        progress = custom_uploader.update_database()
        # Step 3: Check the assignment is what is expected
        time_out = time.time()+10
        while not progress.workflow_state == "completed" and time_out>time.time():
            time.sleep(.1)
            progress = progress.query()
        updated_assignment = custom_uploader.assignment_to_upload
        submission = updated_assignment.get_submission(115753)
        assert submission.score == 2.0

    def test_update_match(self):
        self.uploader.init_course({'canvas_user_id': '114217'})
        self.uploader.parse_form_data()
        progress = self.uploader._submit_grades()
        assignment_match = AssignmentMatch.query.filter_by(nbgrader_assign_name=self.uploader._form_nb_assign_name, course_id=self.uploader._course_id).first()
        self.uploader._update_match(assignment_match, progress)
        db.session.commit()
        match = AssignmentMatch.query.filter_by(nbgrader_assign_name=self.uploader._form_nb_assign_name, course_id=self.uploader._course_id).first()
        assert match.progress_url == progress.url

    
    def test_add_new_match(self):
        custom_uploader = UploadGrades(20774, 92059, 'create', 'Test Assignment 3')
        custom_uploader.init_course({'canvas_user_id': '114217'})
        custom_uploader.parse_form_data()
        progress = custom_uploader._submit_grades()
        before = AssignmentMatch.query.filter_by(nbgrader_assign_name=custom_uploader._form_nb_assign_name, course_id=custom_uploader._course_id).first()
        custom_uploader._add_new_match(progress)
        after = AssignmentMatch.query.filter_by(nbgrader_assign_name=custom_uploader._form_nb_assign_name, course_id=custom_uploader._course_id).first()
        passed = after != before
        db.session.delete(after)
        db.session.commit()
        custom_uploader.assignment_to_upload.delete()
        assert passed
        

    