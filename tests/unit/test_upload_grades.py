from nbgrader_to_canvas.upload_grades import UploadGrades
from nbgrader_to_canvas.models import AssignmentStatus, Users
from nbgrader_to_canvas.canvas import CanvasWrapper
from tests.unit import canvas_students, student_grades, existing_assignment, wipe_db, clear_grades
from tests.unit import FakeProgress, FakeResponse
from unittest.mock import MagicMock
import unittest
import pytest
from nbgrader_to_canvas import db




class TestUploadGrades(unittest.TestCase):

    # Expected setup:
    # assign1 unused
    # Test Assignment 1 deleted and matches removed
    # Test Assignment 2 exists and it's id is given to uploader
    # Test Assignment 3 deleted and matches removed
    @pytest.fixture
    def setup(self):
        wipe_db()
        canvas_wrapper = CanvasWrapper('https://canvas.ucsd.edu', {'canvas_user_id': '114217'})
        canvas = canvas_wrapper.get_canvas()
        course = canvas.get_course(20774)
        assignment2 = course.create_assignment({'name':'Test Assignment 2', 'published':'true', 'assignment_group_id':92059, 'points_possible':6})
        yield assignment2.id

    # Needed to add user to db before testing
    @pytest.fixture
    def user(self):
        old_user = Users.query.filter_by(user_id=114217).first()
        if old_user:
            db.session.delete(old_user)
            db.session.commit()
        self._user = Users(114217,'13171~RcKmrrEpUNajUlnEl3jDVJK3NEvPffOaomiWI2eJB6c6WTp6cKEJEs4gImOZ1B0u',10,'')
        db.session.add(self._user)
        db.session.commit()
        yield self._user
        db.session.delete(self._user)
        db.session.commit()

    @pytest.fixture(autouse = True)
    def uploader(self, user, setup):
        self.uploader = UploadGrades(20774, 92059, setup, 'Test Assignment 2', 0)
        yield self.uploader
    
    def test_init_course_returns_course_for_valid_course_id(self):
        self.uploader.init_course({'canvas_user_id': '114217'}, True)
        assert self.uploader._course.name == 'Canvas Caliper Events Testing'
    
    def test_init_course_raises_error_for_invalid_course_id(self):
        self.uploader._course_id=1234
        try:
            self.uploader.init_course({'canvas_user_id': '114217'}, True)
        except Exception as e:
            return
        assert False

    def test_get_canvas_students(self):
        self.uploader.init_course({'canvas_user_id': '114217'}, True)
        self.uploader._create_assignment_status()
        students = self.uploader._get_canvas_students()
        print(students)
        assert students == canvas_students

    def test_get_student_grades_returns_grades_for_valid_course_name(self):
        self.uploader._create_assignment_status()
        self.uploader._nbgrader_course = 'TEST_NBGRADER'
        self.uploader._num_students = self.uploader._get_num_students(gb='TEST_NBGRADER')
        self.uploader.canvas_students = canvas_students
        grades = self.uploader._get_student_grades(gb='TEST_NBGRADER')
        print(grades)
        assert grades == student_grades
    
    def test_get_student_grades_raises_error_for_invalid_course_name(self):
        self.uploader._course_name = 'invalid name'
        self.uploader._create_assignment_status()
        self.uploader.canvas_students = canvas_students
        try:
            self.uploader._get_student_grades(gb='TEST_NBGRADER')
        except Exception as e:
            print("{}".format(e))
            return
        assert False
    
    def test_get_assignment_returns_assignment_for_valid_form_data(self):
        self.uploader.init_course({'canvas_user_id': '114217'}, True)
        assignment = self.uploader._get_assignment()
        assert assignment.name == existing_assignment

    def test_get_assignment_raises_error_for_invalid_form_data(self):
        self.uploader.init_course({'canvas_user_id': '114217'}, True)
        self.uploader._form_canvas_assign_id = 1234
        try:
            self.uploader._get_assignment()
        except Exception as e:
            print("{}".format(e))
            return
        assert False
    
    def test_create_assignment(self):
        custom_uploader = UploadGrades(20774, 92059, 'create', 'Test Assignment 3', 0)
        custom_uploader.init_course({'canvas_user_id': '114217'}, True)
        assignment = custom_uploader._create_assignment(10)
        name = assignment.name
        assignment.delete()
        assert name == 'Test Assignment 3'


    def test_submit_grades(self):
        self.uploader.init_course({'canvas_user_id': '114217'}, True)
        self.uploader.parse_form_data()
        progress = self.uploader._submit_grades()   
        assert progress.workflow_state == 'completed'

    # Checks the grade of Test Account 333, Test Assignment 1
    def test_grades_match_create(self):
        clear_grades()
        self.uploader.init_course({'canvas_user_id': '114217'}, True)
        # Call upload grades
        custom_uploader = UploadGrades(20774, 92059, 'create', 'Test Assignment 1', 0)
        custom_uploader.init_course({'canvas_user_id': '114217'}, True)
        custom_uploader.parse_form_data()
        custom_uploader.update_database()
        # Check the assignment is what is expected
        
        updated_assignment = custom_uploader.assignment_to_upload
        submission = updated_assignment.get_submission(141753)
        assert submission.score == 2.0    

    # Tests that status is created with proper initial values
    def test_create_status(self):
        self.uploader._create_assignment_status()
        status = AssignmentStatus.query.filter_by(nbgrader_assign_name='Test Assignment 2').first()
        assert status.status == 'Initializing'
    
    # Tests that status is refreshed properly. Uses _setup_status and _refresh_assignment_status
    def test_refresh_status(self):
        test_status = AssignmentStatus(course_id=20774, nbgrader_assign_name='Test Assignment 2', canvas_assign_id='test', status='Bad Status', completion=150, late_penalty=0)
        db.session.add(test_status)
        db.session.commit()
        self.uploader._setup_status()
        status = AssignmentStatus.query.filter_by(nbgrader_assign_name='Test Assignment 2').first()
        assert status.status == 'Initializing'

    # Tests uploading nbgrader assignment 'Test Assignment 1' with canvas assignment 'Week 2: Assignment'
    def test_grades_match_different_names(self):
        custom_uploader = UploadGrades(20774, 92059, 192793, 'Test Assignment 1', 0)
        custom_uploader.init_course({'canvas_user_id': '114217'}, True)
        custom_uploader.parse_form_data()
        custom_uploader.update_database()
        
        # Check the assignment is correct on canvas
        updated_assignment = custom_uploader.assignment_to_upload
        submission = updated_assignment.get_submission(141753)
        assert submission.score == 2.0 
        assert updated_assignment.name == 'Week 2: Assignment'

    # Tests uploading to 'Test Assignment 2' which already is matched to canvas 'Test Assignment 2'
    def test_grades_match_existing(self):
        clear_grades()
        self.uploader.init_course({'canvas_user_id': '114217'}, True)
        self.uploader.parse_form_data()
        self.uploader.update_database()
        # Check the assignment is correct on canvas
        updated_assignment = self.uploader.assignment_to_upload
        submission = updated_assignment.get_submission(141754)
        assert submission.score == 6.0

     # Test comments are deleted
    def test_comments_are_deleted(self):
        self.uploader.init_course({'canvas_user_id': '114217'}, True)
        self.uploader.parse_form_data()
        self.uploader.update_database()
        # assert that a comment exists for Test Assignment 2 for NBStudent_1
        submission = self.uploader.assignment_to_upload.get_submission(141753,include=['submission_comments'])
        assert len(submission.submission_comments) > 0
            
        self.uploader._delete_comments(gb='TEST_NBGRADER')
        submission = self.uploader.assignment_to_upload.get_submission(141753,include=['submission_comments'])
        assert len(submission.submission_comments) == 0
            

    # Test feedback is uploaded for assignment with feedback
    def test_comment_for_feedback(self):
        self.uploader.init_course({'canvas_user_id': '114217'}, True)
        self.uploader.parse_form_data()
        self.uploader.update_database()
        # assert that a comment exists for Test Assignment 2 for NBStudent_1
        submission = self.uploader.assignment_to_upload.get_submission(141753,include=['submission_comments'])
        assert len(submission.submission_comments) > 0

    # Test feedback is not uploaded for assignment without feedback
    def test_no_comment_for_no_feedback(self):
        custom_uploader = UploadGrades(20774, 92059, 'create', 'assign1', 0)
        custom_uploader.init_course({'canvas_user_id': '114217'}, True)
        custom_uploader.parse_form_data()
        custom_uploader.update_database()
        # assert that a comment exists for Test Assignment 2 for NBStudent_1
        submission = custom_uploader.assignment_to_upload.get_submission(141753,include=['submission_comments'])
        assert len(submission.submission_comments) == 0
    