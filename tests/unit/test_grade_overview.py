from nbgrader_to_canvas.grade_overview import GradeOverview
from nbgrader_to_canvas.models import AssignmentMatch, Users
from tests.unit import expected_nbgrader_assignments, expected_canvas_assignments, expected_matches_names, wipe_db
import unittest
import pytest
from nbgrader_to_canvas import canvas, db, app

import time

class TestUploadGrades(unittest.TestCase):

    # Expected setup:
    # All Test Assignments deleted, and matches deleted
    @pytest.fixture
    def setup(self):
        wipe_db()

    # Needed to add user to db before testing
    @pytest.fixture(autouse = True)
    def user(self):
        old_user = Users.query.filter_by(user_id=114217).first()
        if old_user:
            db.session.delete(old_user)
            db.session.commit()
        self._user = Users(114217,'13171~bngbhxjVx3G7sqnWFC3BFs0r9MgN408enlV3I3uN74pCPpjkQvK2bI3eEcStdPH1',10)
        db.session.add(self._user)
        db.session.commit()
        yield self._user
        db.session.delete(self._user)
        db.session.commit()
        
    @pytest.fixture(autouse = True)
    def uploader(self, user, setup):
        self.grade_overview = GradeOverview()
        self.grade_overview.course_id = 20774
        self.grade_overview.group = 92059
        yield None
        wipe_db()

    def test_init_canvas(self):
        self.grade_overview._init_canvas({'canvas_user_id': '114217'})
        assert self.grade_overview._course.name == 'Canvas Caliper Events Testing'

    def test_get_nbgrader_assignments(self):
        assignments = self.grade_overview._get_nbgrader_assignments()
        names = {assignment.name for assignment in assignments}
        assert names == expected_nbgrader_assignments
    
    def test_get_assignment_group_id(self):
        self.grade_overview._init_canvas({'canvas_user_id': '114217'})
        group_id = self.grade_overview._get_assignment_group_id()
        assert group_id == 92059

    def test_get_canvas_assignments(self):
        self.grade_overview._init_canvas({'canvas_user_id': '114217'})
        assignments = self.grade_overview._get_canvas_assignments()
        assert set(assignments.values()) == set(expected_canvas_assignments.values())

    
    def test_cleanup_assignment_matches(self):
        self.grade_overview._init_canvas({'canvas_user_id': '114217'})
        self.grade_overview.nb_assignments = self.grade_overview._get_nbgrader_assignments()
        self.grade_overview.canvas_assignments = self.grade_overview._get_canvas_assignments()
        fakeMatch = AssignmentMatch(course_id=20774, nbgrader_assign_name='Test Assignment 3',
                    canvas_assign_id=10, upload_progress_url='fake progress', last_updated_time=10)
        db.session.add(fakeMatch)
        db.session.commit()
        self.grade_overview._cleanup_assignment_matches()
        match = AssignmentMatch.query.filter_by(nbgrader_assign_name='Test Assignment 3').first()
        assert match == None

    def test_match_assignments(self):
        self.grade_overview.nb_assignments = self.grade_overview._get_nbgrader_assignments()
        matches = self.grade_overview._match_assignments()
        names = {m for m in matches}
        print(names)
        assert names == expected_matches_names