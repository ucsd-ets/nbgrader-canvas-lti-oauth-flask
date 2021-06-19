from nbgrader_to_canvas.grade_overview import GradeOverview
from nbgrader_to_canvas.models import AssignmentMatch, Users
from canvasapi import Canvas
from flask import session
from . import expected_nbgrader_assignments, expected_canvas_assignments
import unittest
import pytest
from nbgrader_to_canvas import db, app

import time

class TestUploadGrades(unittest.TestCase):

    # @pytest.fixture(autouse = True)
    # def user(self):
    #     self._user = Users(114217,'13171~qKHvThhYQrIr0HfTicEEfmBD1DeLG7YM7FZD4RMtf5iFfoyr1eFPKy7lR8kWxJWT',10)
    #     db.session.add(self._user)
    #     db.session.commit()
    #     yield self._user
    #     db.session.delete(self._user)
    #     db.session.commit()
        
    @pytest.fixture(autouse = True)
    def uploader(self):
        self.grade_overview = GradeOverview()
        self.grade_overview.course_id = 20774

    def test_init_canvas(self):
        self.grade_overview._init_canvas({'canvas_user_id': '114217'})
        assert self.grade_overview._course.name == 'ET-MCC-CCET_FA20 Canvas Caliper Events Testing'

    def test_get_nbgrader_assignments(self):
        assignments = self.grade_overview._get_nbgrader_assignments()
        assert assignments == expected_nbgrader_assignments
    
    def test_get_assignment_group_id(self):
        self.grade_overview._init_canvas({'canvas_user_id': '114217'})
        group_id = self.grade_overview._get_assignment_group_id()
        assert group_id == 92059

    def test_get_canvas_assignments(self):
        assignments = self.grade_overview._get_canvas_assignments(92059)
        assert assignments == expected_canvas_assignments

    def test_cleanup_assignment_matches(self):
        nb_assignments = self.grade_overview._get_nbgrader_assignments()
        # add 'Fake Assignment' to nb_assignments
        fakeMatch = AssignmentMatch(course_id=20774, nbgrader_assign_name='Fake Assignment',
                    canvas_assign_id='fake', upload_progress_url='fake', last_updated_time='fake')
        db.session.add(fakeMatch)
        # call cleanup_assignment_matches and assert fakeMatch is no longer in the db after
        assert False

    def test_match_assignments(self):
        assert False