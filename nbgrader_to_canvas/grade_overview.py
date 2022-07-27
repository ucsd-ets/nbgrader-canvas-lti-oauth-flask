from .utils import return_error, check_valid_user, open_circuit
from flask import Blueprint, Response, render_template, session, request, url_for, redirect
from pylti.flask import lti

import os
from os import path

from nbgrader_to_canvas import app, db, settings


from nbgrader.api import Gradebook
from .models import AssignmentStatus

from canvasapi.exceptions import InvalidAccessToken
from .upload_grades import current_uploads
from .canvas import CanvasWrapper, Token
from .utils import open_gradebook

from circuitbreaker import circuit

grade_overview_blueprint = Blueprint('grade_overview', __name__)



@lti(request='session', role='staff')
def get_canvas_id(lti=lti):
    """
    Get the canvas course id
    """
    try:
        out = session['course_id']
        return out
    except Exception as ex:
        app.logger.error("Error getting course id: {}".format(ex))
        return "error"



@grade_overview_blueprint.route("/grade_overview", methods=['GET', 'POST'])
@circuit(failure_threshold=1, fallback_function=open_circuit)
@check_valid_user
def grade_overview(progress = None):
    try:
        
        grade_overview = GradeOverview()
        grade_overview.init_assignments()
        grade_overview.setup_matches()

        if request.method == 'POST':
            return redirect(url_for('grade_overview.grade_overview'))
        
        
        return Response(
                render_template('overview.htm.j2', nb_assign=grade_overview.nb_assignments, cv_assign=grade_overview.canvas_assignments,
                                nb_matches=grade_overview.nb_matches, cv_matches=grade_overview.cv_matches,
                                course_id=grade_overview.course_id, group=grade_overview.group, progress = progress)
            )
    except KeyError as keyE:
        app.logger.error("KeyError: " + str(keyE))
        app.logger.error(os.getcwd())

        msg = (
            'Issues with querying the database for the canvas_user_id. '
            'Cannot call functions on the canvas object. '
            'Delete user from users table or wait for token refresh'
        )
        raise Exception(msg)

    except InvalidAccessToken as eTok:
        app.logger.error("InvalidAccessToken: " + str(eTok))
        app.logger.error(session['api_key'])
        app.logger.error(os.getcwd())

        token = Token(session,session['canvas_user_id'])
        if not token.refresh():
            raise Exception('Access token not refreshing.')
        
        return redirect(url_for('grade_overview.grade_overview'))

    except Exception as e:
        app.logger.error("Exception unknown: " + str(type(e)) + str(e))
        app.logger.error(os.getcwd())
        app.logger.error(str(type(e)) + " error occurred.")
        msg = (
            'Issues with the grade_overview file:<br>'+str(e)
        )
        return return_error(msg)

    


class GradeOverview:

    def init_assignments(self, flask_session = session):
        self.course_id = get_canvas_id()
        self._init_canvas(flask_session)
        self._setup_gradebook_path()
        self.nb_assignments = self._get_nbgrader_assignments(gb=self._nbgrader_course)
        self.group = self._get_assignment_group_id()
        self.canvas_assignments = self._get_canvas_assignments()
        
    
    def setup_matches(self):
        '''Prunes database for deleted assignments then returns valid matches'''
        self._cleanup_assignment_matches()
        self.nb_matches = self._match_nb_assignments()
        self.cv_matches = self._match_cv_assignments()

    def _init_canvas(self, flask_session = session):
        self._canvas_wrapper = CanvasWrapper(settings.API_URL, flask_session)
        self._canvas = self._canvas_wrapper.get_canvas()
        self._course = self._canvas.get_course(self.course_id)

    def _setup_gradebook_path(self):
        if self._course.course_code == 'ET-MCC-CCET_FA20':
            self._nbgrader_course = 'TEST_NBGRADER'
        else:
            self._nbgrader_course = self._course.course_code
        if not path.exists("/mnt/nbgrader/"+self._nbgrader_course+"/grader/gradebook.db"):
            print("Gradebook missing for: {}".format(self._nbgrader_course))
            raise Exception("Gradebook missing for: {}".format(self._nbgrader_course))
    
    @open_gradebook
    def _get_nbgrader_assignments(self,gb):
        '''Get the nbgrader_assignments from the course gradebook'''
        return gb.assignments

    def _get_assignment_group_id(self):
        assignment_groups = self._course.get_assignment_groups()

        for ag in assignment_groups:
            if (ag.name == "Assignments"):
                return ag.id

    def _get_canvas_assignments(self):
        '''Returns a list of assignments for given course and group as a dict {assignment_id:assignment_name}'''
        assignments = self._course.get_assignments_for_group(self.group)
        canvas_assignments = {a.id:a.name for a in assignments}
        return canvas_assignments
    
    def _cleanup_assignment_matches(self):
        '''
        Check if there's a thread running uploading grades with the assignment.name. If it is then leave the match.
        If not and it isn't uploaded, then faile the match.
        If it is uploaded, check if match.canvas_assign_id matches to an assignment. If it doesn't, delete match.
        '''
        for assignment in self.nb_assignments:
            match = AssignmentStatus.query.filter_by(nbgrader_assign_name=assignment.name, course_id=self.course_id).first()
            if not match or assignment.name in current_uploads or match.status == "Failed":
                continue
            if not match.status == "Uploaded":
                match.status = "Failed"
                match.completion = 0
            elif int(match.canvas_assign_id) not in self.canvas_assignments:
                db.session.delete(match)
        db.session.commit()

    def _match_nb_assignments(self):
        nb_matches = {assignment.name:AssignmentStatus.query.filter_by(nbgrader_assign_name=assignment.name, course_id=self.course_id).first()
                                                                for assignment in self.nb_assignments}
        return nb_matches

    def _match_cv_assignments(self):
        cv_matches = {self.canvas_assignments[id]:AssignmentStatus.query.filter_by(canvas_assign_id=str(id), course_id=self.course_id).first()
                                                                for id in self.canvas_assignments}
        return cv_matches
