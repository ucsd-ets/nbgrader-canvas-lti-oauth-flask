from types import GetSetDescriptorType
from flask import Blueprint, render_template, session, request
from pylti.flask import lti

from .utils import get_canvas, error
from . import app
from . import settings
from nbgrader.api import Gradebook, MissingEntry

import json
import logging
import sys
import jsonpickle
upload_grades_blueprint = Blueprint('upload_grades', __name__)

# Web Views / Routes
@upload_grades_blueprint.route('/upload_grades', methods=['GET', 'POST'])
@lti(error=error, request='session', role='staff', app=app)
def upload_grades(lti=lti):

    import sys
    import os
    import canvasapi
    import pytest
    # Import the Canvas class
    from canvasapi.assignment import (
        Assignment,
        AssignmentGroup,
        AssignmentOverride,
        AssignmentExtension,
    )
    from canvasapi.progress import Progress
    from canvasapi.course import Course

    # TODO: modify below to redirect to status page after POST, see
    # https://stackoverflow.com/questions/31542243/redirect-to-other-view-after-submitting-form

    args = request.args.to_dict()

    course_id = session['course_id']

    # initialize a new canvasapi Canvas object
    canvas = get_canvas()

    # canvasapi debugging info https://github.com/ucfopen/canvasapi/blob/master/docs/debugging.rst
    logger = logging.getLogger("canvasapi")
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    handler.setLevel(logging.ERROR)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)

    # to do error handling
    #if canvas is None:
    #    courses = None
    #else:
    #    courses = canvas.get_courses()
    
    app.logger.info("request.method:")
    app.logger.info(request.method)

    app.logger.error("session grades_submitted:")
    app.logger.error(session['grades_submitted'])

    # redirect with preserved POST method: submit grade
    if request.method == 'POST' and session['grades_submitted'] is False:

        course = canvas.get_course(course_id)
        canvas_assignments = course.get_assignments()
        canvas_users = course.get_users()
        
        canvas_students = {}
        # TODO: modify to only get active users
        for canvas_user in canvas_users:
            if hasattr(canvas_user, "login_id") and canvas_user.login_id is not None:
                canvas_students[canvas_user.login_id]=canvas_user.id     

        #
        # nbgrader code
        #

        with Gradebook("sqlite:////mnt/nbgrader/TEST_NBGRADER/grader/gradebook.db") as gb:

            # create a list of dictionaries for each submission
            nb_assignments = gb.assignments
            nb_students = gb.students
            nbgraderdata = {}

            # create a list of assignments or students to grade
            # if lists are empty, all students are selected
            # NEED to find a way to populate this - most likely on flask application?? #
            nb_assignmentList = []
            nb_studentList = []

            # loop over all nb assignments
            for nb_assignment in nb_assignments:

                app.logger.debug("nb assignment name:")
                app.logger.debug(nb_assignment.name)
                
                nb_grade_data = {}

                # only continue if nb assignment is required (pj: ?)
                if nb_assignmentList and nb_assignment.name not in nb_assignmentList:
                    continue

                # loop over each nb student
                for nb_student in nb_students:

                    #app.logger.debug("student id:")
                    #app.logger.debug(nb_student.id)

                    # only continue if student is required (pj: ?)
                    if nb_studentList and nb_student.id not in nb_studentList:
                        continue

                    # ceate dict for grade_data, with nested dict {student id: {score}}
                    nb_student_and_score = {}            

                    # Try to find the submission in the (pj: nbgrader?) database. If it doesn't exist, the
                    # MissingEntry exception will be raised and we assign them a score of None.

                    try:
                        nb_submission = gb.find_submission(nb_assignment.name, nb_student.id)
                    except MissingEntry:
                        nb_student_and_score['posted_grade'] = None
                    else:
                        nb_student_and_score["posted_grade"] = nb_submission.score
                        #app.logger.debug("sub name:")
                        #app.logger.debug(nb_submission.name)
                        #app.logger.debug("sub id:")
                        #app.logger.debug(nb_submission.id)
                        #app.logger.debug("sub score:")
                        #app.logger.debug(nb_submission.score)

                    # student.id will give us student's username, ie shrakibullah. we will need to compare this to
                    # canvas's login_id instead of user_id

                    # convert nbgrader username to canvas id (integer)
                    #nb_grade_data[nb_student.id] = nb_student_and_score
                    canvas_student_id = canvas_students[nb_student.id]
                    nb_grade_data[canvas_student_id] = nb_student_and_score

                nbgraderdata[nb_assignment] = nb_grade_data
                match = False

                # loop over canvas assignments, upload submissions if name matches
                # TODO: check for dup assignment names
                for canvas_assignment in canvas_assignments:
                    if nb_assignment.name == canvas_assignment.name:
                        app.logger.debug("canvas assignment name match; id:")
                        app.logger.debug(canvas_assignment.id)
                        app.logger.debug("canvas assignment name match; name:")
                        app.logger.debug(canvas_assignment.name)
                        app.logger.debug("upload submissions for existing canvas assignment")

                        #json_str = json.dumps(nbgraderdata[nb_assignment])
                        #app.logger.debug("json:")
                        #app.logger.debug(json_str)
                        app.logger.debug("grade data to upload:")
                        app.logger.debug(nbgraderdata[nb_assignment])

                        
                        assignment_to_upload = course.get_assignment(canvas_assignment.id)                

                        # check if published, if not, publish?
                        progress = assignment_to_upload.submissions_bulk_update(grade_data=nbgraderdata[nb_assignment])
                        progress = progress.query()
                        # TODO: array of progress objects
                        # https://stackoverflow.com/questions/61415988/flask-storing-get-and-update-list-in-session-using-flask-session
                        session['progress_json']=jsonpickle.encode(progress)

                        # note we found a match, exit canvas assignment loop
                        match = True
                        break
                
                # no match found and instructor oks blind submissions - assignment does not exist in canvas, 
                # create it (name it with nb assignment name) and upload submissions
                if match == False and nb_assignment.name:
                    app.logger.debug("upload submissions for non-existing canvas assignment; will be named:")
                    app.logger.debug(nb_assignment.name)                

                    #json_str = json.dumps(nbgraderdata[nb_assignment])
                    #app.logger.debug("json:")
                    #app.logger.debug(json_str)

                    # create new assignments as published
                    new_assignment_to_upload = course.create_assignment({'name':nb_assignment.name, 'published':'true'})
                    progress = new_assignment_to_upload.submissions_bulk_update(grade_data=nbgraderdata[nb_assignment])
                    progress = progress.query()
                    session['progress_json']=jsonpickle.encode(progress)

        session['grades_submitted'] = True
        return render_template('upload_grades.htm.j2', progress=progress, BASE_URL=settings.BASE_URL)
    
    # non-POST: just dispay status of assignment upload(s)
        
    app.logger.info("convert progress obj")

    progress = jsonpickle.decode(session['progress_json'])
    progress = progress.query()

    return render_template('upload_grades.htm.j2', progress=progress, BASE_URL=settings.BASE_URL)
