# import os
# import tempfile

# import pytest

# import nbgrader_to_canvas
from nbgrader_to_canvas.canvas import CanvasWrapper
from nbgrader_to_canvas import db
from nbgrader_to_canvas.models import AssignmentMatch
import time


# @pytest.fixture
# def client():
#     with nbgrader_to_canvas.app.test_client() as client:
#         yield client

# Creates a standard clean slate for all tests to start from
def wipe_db():
    # clear AssignmentMatch
    for match in AssignmentMatch.query.filter_by():
        db.session.delete(match)
    # wipe Test Assignment 1-3, and assign1
    canvas_wrapper = CanvasWrapper('https://ucsd.test.instructure.com', {'canvas_user_id': '114217'})
    canvas = canvas_wrapper.get_canvas()
    course = canvas.get_course(20774)
    
    for assignment in course.get_assignments_for_group(92059):
        if 'Test Assignment' in assignment.name or assignment.name == 'assign1':
            assignment.delete()

    db.session.commit()

def clear_grades():
    canvas_wrapper = CanvasWrapper('https://ucsd.test.instructure.com', {'canvas_user_id': '114217'})
    canvas = canvas_wrapper.get_canvas()
    course = canvas.get_course(20774)
    users = course.get_users()
    clear_grades = {user.id: {'posted_grade':''} for user in users}
    for assignment in course.get_assignments_for_group(92059):
        if assignment.published:
            try:
                progress = assignment.submissions_bulk_update(grade_data=clear_grades)
                timeout = time.time()+10
                while not progress.workflow_state == 'completed' and timeout > time.time():
                    progress = progress.query()
                    time.sleep(.1)
                    if progress.workflow_state == 'failed':
                        print('failed')
                        break
                print(assignment.name, progress.workflow_state)
            except:
                print(assignment.name)
             
