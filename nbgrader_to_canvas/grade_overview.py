from flask import Blueprint, Response, render_template, session, request, url_for, redirect
from pylti.flask import lti

import os


from . import app, db, settings
from .utils import return_error, error

from nbgrader.api import Gradebook
from .models import AssignmentMatch, AssignmentStatus

from canvasapi.exceptions import InvalidAccessToken
from .upload_grades import UploadGrades, upload_grades
from .canvas import CanvasWrapper
import time

grade_overview_blueprint = Blueprint('grade_overview', __name__)


# @grade_overview_blueprint.route("/grade_overview", methods=['GET', 'POST'])
# def grade_overview(progress = None):
#     """
#     Renders the main template for the flask application.
#     grade_overview can be viewed at overview.htm.j2
#     """
    

#     try:
#         nb_assignments = get_nbgrader_assignments()
#         course_id = get_canvas_id()
#         group = get_assignment_group_id()
#         canvas_assignments = get_canvas_assignments(course_id, group)


#         if request.method == 'POST':
#             progress = upload_grades(course_id, group)
#             return redirect(url_for('grade_overview.grade_overview'))
        
#         cleanup_assignment_matches(nb_assignments,course_id,canvas_assignments)
#         db_matches = match_assignments(nb_assignments, course_id)
        
        

#         return Response(
#             render_template('overview.htm.j2', nb_assign=nb_assignments, cv_assign=canvas_assignments,
#                              db_matches=db_matches, course_id=course_id, progress = progress)
#         )

#     except KeyError as keyE:
#         app.logger.error("KeyError: " + str(keyE))
#         app.logger.error(os.getcwd())

#         msg = (
#             'Issues with querying the database for the canvas_user_id. '
#             'Cannot call functions on the canvas object. '
#             'Delete user from users table or wait for token refresh'
#         )
#         return return_error(msg)

#     except InvalidAccessToken as eTok:
#         app.logger.error("InvalidAccessToken: " + str(eTok))
#         app.logger.error(os.getcwd())

#         msg = (
#             'Issues with access token.'
#         )
#         return return_error(msg)

#     except Exception as e:
#         app.logger.error("Exception unknown: " + str(type(e)) + str(e))
#         app.logger.error(os.getcwd())
#         app.logger.error(str(type(e)) + " error occurred.")
#         msg = (
#             'Issues with the grade_overview file. Please refresh and try again. '
#             'If this error persists, please contact support.'
#         )
#         return return_error(msg)


# def get_nbgrader_assignments(course="TEST_NBGRADER"):
#     """
#     Get the nbgrader_assignments from the course gradebook
#     """
#     # get the gradebook and return the assignments
#     with Gradebook("sqlite:////mnt/nbgrader/"+course+"/grader/gradebook.db") as gb:
#         return gb.assignments


# def get_assignment_group_id():

#     # initialize a new canvasapi Canvas object
#     canvas = get_canvas()
    
#     # find the "Assignments" group
#     course = canvas.get_course(get_canvas_id())
#     assignment_groups = course.get_assignment_groups()

#     for ag in assignment_groups:
#         if (ag.name == "Assignments"):
#             return course.get_assignment_group(ag.id).id


# def get_canvas_assignments(course_id, group):
#     """
#     Get the assignments for the Canvas course
#     """
#     # initialize a new canvasapi Canvas object
#     canvas = get_canvas()

#     # get canvas assignment groups from course
#     course = canvas.get_course(course_id)
#     assignments = course.get_assignments_for_group(group)

#     # have the id:name key:value pair for each course assignment
#     canvas_assignments = {a.id:a.name for a in assignments}

#     return canvas_assignments
    

# def match_assignments(nb_assignments, course_id):
#     """
#     Check sqlalchemy table for match with nbgrader assignments from a specified course. Creates a dictionary with nbgrader
#         assignments as the key
#     If match is found, query the entry from the table and set as the value.
#     Else, set the value to None
#     """
#     # for assignment in nb_assignments:
#     #     app.logger.debug(assignment.name) 
    
#     nb_matches = {assignment.name:AssignmentMatch.query.filter_by(nbgrader_assign_name=assignment.name, course_id=course_id).first()
#                                                             for assignment in nb_assignments}
#     return nb_matches

# # Go through matches that correspond to a nb_assignment and verify the corresponding canvas assignment still exists.
# # If canvas assignment no longer exists, remove match from database
# def cleanup_assignment_matches(nb_assignments, course_id, canvas_assignments):
#     for assignment in nb_assignments:
#         match = AssignmentMatch.query.filter_by(nbgrader_assign_name=assignment.name, course_id=course_id).first()
#         if match and match.canvas_assign_id not in canvas_assignments:
#             app.logger.debug("Assignment Match removed: {}, {}".format(assignment,match.canvas_assign_id))
#             db.session.delete(match)
#             db.session.commit()


@lti(request='session', role='staff')
def get_canvas_id(lti=lti):
    """
    Get the canvas course id
    """
    return session['course_id']



@grade_overview_blueprint.route("/grade_overview", methods=['GET', 'POST'])
def grade_overview(progress = None):

    try:
        
        grade_overview = GradeOverview()
        grade_overview.init_assignments()
        
        db_matches = grade_overview.get_matches()
        app.logger.debug('{}'.format(grade_overview.nb_assignments))

        if request.method == 'POST':
            #progress = upload_grades(grade_overview.course_id, grade_overview.group)
            return redirect(url_for('grade_overview.grade_overview'))
        
        
        return Response(
                render_template('overview.htm.j2', nb_assign=grade_overview.nb_assignments, cv_assign=grade_overview.canvas_assignments,
                                db_matches=db_matches, course_id=grade_overview.course_id, group=grade_overview.group, progress = progress)
            )
    except KeyError as keyE:
        app.logger.error("KeyError: " + str(keyE))
        app.logger.error(os.getcwd())

        msg = (
            'Issues with querying the database for the canvas_user_id. '
            'Cannot call functions on the canvas object. '
            'Delete user from users table or wait for token refresh'
        )
        return return_error(msg)

    except InvalidAccessToken as eTok:
        app.logger.error("InvalidAccessToken: " + str(eTok))
        app.logger.error(session['api_key'])
        app.logger.error(os.getcwd())

        msg = (
            'Issues with access token.'
        )
        return return_error(msg)

    except Exception as e:
        app.logger.error("Exception unknown: " + str(type(e)) + str(e))
        app.logger.error(os.getcwd())
        app.logger.error(str(type(e)) + " error occurred.")
        msg = (
            'Issues with the grade_overview file. Please refresh and try again. '
            'If this error persists, please contact support.'
        )
        return return_error(msg)

    


class GradeOverview:

    # Initializes stuff. Move to __init__ after testing. Remove defaults after testing
    def init_assignments(self, flask_session = session):
        self.course_id = get_canvas_id()
        self._init_canvas(flask_session)
        self.nb_assignments = self._get_nbgrader_assignments()
        self.group = self._get_assignment_group_id()
        self.canvas_assignments = self._get_canvas_assignments()
    
    # Prunes database for deleted assignments then returns valid matches
    def get_matches(self):
        self._cleanup_assignment_matches()
        return self._match_assignments()

    def _init_canvas(self, flask_session = session):
        self._canvas_wrapper = CanvasWrapper(settings.API_URL, flask_session)
        self._canvas = self._canvas_wrapper.get_canvas()
        self._course = self._canvas.get_course(self.course_id)

    # Get the nbgrader_assignments from the course gradebook
    def _get_nbgrader_assignments(self, course="TEST_NBGRADER"):
        with Gradebook("sqlite:////mnt/nbgrader/"+course+"/grader/gradebook.db") as gb:
            return gb.assignments

    def _get_assignment_group_id(self):
        assignment_groups = self._course.get_assignment_groups()

        for ag in assignment_groups:
            if (ag.name == "Assignments"):
                # if errors, try self._course.get_assignment_group(ag.id).id
                return ag.id

    # Returns a list of assignments for given course and group as a dict {assignment_id:assignment_name}
    def _get_canvas_assignments(self):
        assignments = self._course.get_assignments_for_group(self.group)
        canvas_assignments = {a.id:a.name for a in assignments}
        return canvas_assignments
    
    # Go through matches that correspond to a nb_assignment and verify the corresponding canvas assignment still exists.
    # If canvas assignment no longer exists, remove match from database
    def _cleanup_assignment_matches(self):
        for assignment in self.nb_assignments:
            match = AssignmentMatch.query.filter_by(nbgrader_assign_name=assignment.name, course_id=self.course_id).first()
            if match and match.canvas_assign_id not in self.canvas_assignments:
                app.logger.debug("Assignment Match removed: {}, {}".format(assignment,match.canvas_assign_id))
                db.session.delete(match)
                status = AssignmentStatus.query.filter_by(nbgrader_assign_name=assignment.name, course_id=self.course_id).first()
                if status:
                    db.session.delete(status)
        db.session.commit()

    # Finds entries in db that match given nb_assignments to canvas assignments. Returns dict of {assignment_name: AssignmentMatch}.
    # If no match found, pair name with None.
    # Note that this queries a db of matches and doesn't directly find matches between canvas and nb_grader.
    # Can result in unexpected behavior if assignment is deleted without db being updated.
    def _match_assignments(self):
        nb_matches = {assignment.name:AssignmentMatch.query.filter_by(nbgrader_assign_name=assignment.name, course_id=self.course_id).first()
                                                                for assignment in self.nb_assignments}
        return nb_matches