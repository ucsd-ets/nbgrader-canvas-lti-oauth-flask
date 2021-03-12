from flask import Blueprint, render_template, session, request
from pylti.flask import lti

from .utils import get_canvas, error
from . import app
from . import settings
from nbgrader.api import Gradebook, MissingEntry

import json
import logging
import sys
upload_grades_blueprint = Blueprint('upload_grades', __name__)

# Web Views / Routes
@upload_grades_blueprint.route('/upload_grades', methods=['GET'])
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

    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    # to do error handling
    #if canvas is None:
    #    courses = None
    #else:
    #    courses = canvas.get_courses()

    course = canvas.get_course(course_id)
    #NBGRADER_ASSIGN1_ID = 277845 # canvas "nbgrader assign 1"
    #TESTACCT3_USER_ID = 115753    
    #assignment = course.get_assignment(NBGRADER_ASSIGN1_ID)
    # ASK about assignment submission type (external tool)
    # TODO get assignments from canvas first
    # if there is an nbgrader assignment id that is not in canvas,
    # what do we use as id?

    # this is what below data structure looks like in canvasapi.requester debug stmt:
    # DEBUG - Data: [('grade_data[115753][posted_grade]', 97)]
    # same for json generated from nbgrader:
    # DEBUG - Data: [('grade_data', '{"90840": {"posted_grade": 4.0}, "114262": {"posted_grade": 2.0}}')]
    #progress = assignment.submissions_bulk_update(
    #        grade_data={TESTACCT3_USER_ID: {"posted_grade": 97}}
    #    )
    #progress = progress.query()

    course = canvas.get_course(course_id)
    canvas_assignments = course.get_assignments()
    canvas_users = course.get_users()
    
    canvas_students = {}
    # TODO: modify to only get active users
    for canvas_user in canvas_users:
        if hasattr(canvas_user, "login_id") and canvas_user.login_id is not None:
            canvas_students[canvas_user.login_id]=canvas_user.id

            app.logger.info("canvas user login id:")
            app.logger.info(canvas_user.login_id)    
            app.logger.info("canvas user id:")
            app.logger.info(canvas_user.id)        

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

            app.logger.info("nb assignment name:")
            app.logger.info(nb_assignment.name)
            
            nb_grade_data = {}

            # only continue if nb assignment is required (pj: ?)
            if nb_assignmentList and nb_assignment.name not in nb_assignmentList:
                continue

            # loop over each nb student
            for nb_student in nb_students:

                app.logger.info("student id:")
                app.logger.info(nb_student.id)

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
                    app.logger.info("sub name:")
                    app.logger.info(nb_submission.name)
                    app.logger.info("sub id:")
                    app.logger.info(nb_submission.id)
                    app.logger.info("sub score:")
                    app.logger.info(nb_submission.score)

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
                    app.logger.info("canvas assignment name match; id:")
                    app.logger.info(canvas_assignment.id)
                    app.logger.info("canvas assignment name match; name:")
                    app.logger.info(canvas_assignment.name)
                    app.logger.info("upload submissions for existing canvas assignment")

                    #json_str = json.dumps(nbgraderdata[nb_assignment])
                    #app.logger.info("json:")
                    #app.logger.info(json_str)
                    app.logger.info("grade data to upload:")
                    app.logger.info(nbgraderdata[nb_assignment])

                    
                    assignment_to_upload = course.get_assignment(canvas_assignment.id)                

                    # check if published, if not, publish?
                    progress = assignment_to_upload.submissions_bulk_update(grade_data=nbgraderdata[nb_assignment])
                    progress = progress.query()

                    # note we found a match, exit loop
                    match = True
                    break
            
            # no match found and instructor oks blind submissions - assignment does not exist in canvas, 
            # create it (name it with nb assignment name) and upload submissions
            if match == False and nb_assignment.name:
                app.logger.info("upload submissions for non-existing canvas assignment; will be named:")
                app.logger.info(nb_assignment.name)                

                #json_str = json.dumps(nbgraderdata[nb_assignment])
                #app.logger.info("json:")
                #app.logger.info(json_str)

                # create new assignments as published
                new_assignment_to_upload = course.create_assignment({'name':nb_assignment.name, 'published':'true'})
                progress = new_assignment_to_upload.submissions_bulk_update(grade_data=nbgraderdata[nb_assignment])
                progress = progress.query()
    
    return render_template('upload_grades.htm.j2', progress=progress, BASE_URL=settings.BASE_URL)
