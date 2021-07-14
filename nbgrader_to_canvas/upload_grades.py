from types import GetSetDescriptorType
from typing import Counter
from flask import Blueprint, render_template, session, request, redirect, url_for
from pylti.flask import lti

from .utils import error
from . import app, db
from . import settings
from nbgrader.api import Gradebook, MissingEntry
from .models import AssignmentMatch, AssignmentStatus
from .canvas import CanvasWrapper
from threading import Thread

import datetime
import requests

import json
import logging
import sys
import jsonpickle

import sys
import os
import canvasapi
import pytest
import asyncio
import time
#  Import the Canvas class
from canvasapi.assignment import (
    Assignment,
    AssignmentGroup,
    AssignmentOverride,
    AssignmentExtension,
)
from canvasapi.progress import Progress
from canvasapi.course import Course

from nbgrader_to_canvas import canvas

upload_grades_blueprint = Blueprint('upload_grades', __name__)

# Web Views / Routes
# @upload_grades_blueprint.route('/upload_grades', methods=['GET', 'POST'])
# @lti(error=error, request='session', role='staff', app=app)
# def upload_grades(course_id, group, course_name="TEST_NBGRADER", lti=lti):


#     # TODO: modify below to redirect to status page after POST, see
#     # https://stackoverflow.com/questions/31542243/redirect-to-other-view-after-submitting-form

#     args = request.args.to_dict()

#     app.logger.info("course_id: {}".format(course_id))
#     app.logger.info("group: {}".format(group))

#     # initialize a new canvasapi Canvas object
#     canvas = get_canvas()
#     course = canvas.get_course(course_id)

#     app.logger.info("course: {}".format(course))

#     progress = None

#     # canvasapi debugging info https://github.com/ucfopen/canvasapi/blob/master/docs/debugging.rst
#     canvasapi_logger = logging.getLogger("canvasapi")
#     canvasapi_handler = logging.StreamHandler(sys.stdout)
#     canvasapi_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

#     canvasapi_handler.setLevel(logging.ERROR)
#     canvasapi_handler.setFormatter(canvasapi_formatter)
#     canvasapi_logger.addHandler(canvasapi_handler)
#     canvasapi_logger.setLevel(logging.ERROR)

#     # to do error handling
#     #if canvas is None:
#     #    courses = None
#     #else:
#     #    courses = canvas.get_courses()
#     app.logger.setLevel(logging.DEBUG)
#     app.logger.debug("request.method:")
#     app.logger.debug(request.method)

#     #
#     # get assignment match info from psql table
#     # TODO: fetch for all
#     #assignment_match = Users.query.filter_by(user_id=int(session['canvas_user_id'])).first()

#     # ADD JS TO VIEW:
#     # 1) every 10 seconds, update the status of any assignments in the UI that have a status of queued or running in sqlalchemy assignments_table
#     #    a) fetch the progress url from the sqlalchemy assignments_table, get the status
#     # 2) if status is different than status in db, update db and UI with this new value 

#     # POST: 
#     # 1) submit assignment using submissions_bulk_update
#     #    a) find the nbgrader assignment by name
#     #
#     # 2) insert/update sqlalchemy assignment_match table for the submitted nbgrader assignment:
#     #    a) if nbgrader assignment does not exist: insert row with matching nbgrader/canvas assignment IDs, upload progress object url (progress.url) 
#     #       and upload status string
#     #    b) if it does: check that the canvas assignment id they submitted matches the one in the db.  if it doesn't, return an error.  update the
#     #       row with the new progress object url and progress object status (progress.status)
#     #       progress object status types: the state of the job one of 'queued', 'running', 'completed', 'failed'

#     if request.method == 'POST':
#         canvas_assignment_id = None
#         assignment_to_upload = None

#         app.logger.debug("form_nb_assign_name:")
#         app.logger.debug(request.form.get('form_nb_assign_name'))
#         app.logger.debug("form_canvas_assign_id:")
#         app.logger.debug(request.form.get('form_canvas_assign_id'))

#         form_nb_assign_name = request.form.get('form_nb_assign_name')
#         form_canvas_assign_id = request.form.get('form_canvas_assign_id')

#         assignment_match = AssignmentMatch.query.filter_by(nbgrader_assign_name=form_nb_assign_name, course_id=course_id).first()
#         app.logger.debug("assignment match:")
#         app.logger.debug(assignment_match)
#         # app.logger.debug("assignment match url:")
#         # app.logger.debug(assignment_match.progress_url)
#         # upload_url=assignment_match.progress_url
        
#         canvas_users = course.get_users()        
#         canvas_students = {}
#         # TODO: modify to only get active users
#         for canvas_user in canvas_users:
#             if hasattr(canvas_user, "login_id") and canvas_user.login_id is not None:
#                 canvas_students[canvas_user.login_id]=canvas_user.id  
                
#                 # app.logger.debug("canvas user login id:")
#                 # app.logger.debug(canvas_user.login_id)   
#                 # app.logger.debug("canvas user id:")
#                 # app.logger.debug(canvas_user.id)   

#         #
#         #  get nbgrader info
#         #

#         with Gradebook("sqlite:////mnt/nbgrader/"+course_name+"/grader/gradebook.db") as gb:
#         #with Gradebook("sqlite:////mnt/nbgrader/BIPN162_S120_A00/grader/gradebook.db") as gb:

#             # get the nbgrader assignment from the nbgradebook for the 
#             # nbgrader assignment submitted in the form
#             # TODO: handle exception here
#             nb_assignment = gb.find_assignment(form_nb_assign_name)

#             # TODO: can we change this to just get the students for this assignment?
#             nb_students = gb.students            
#             nb_grade_data = {}

#             # loop over each nb student
#             for nb_student in nb_students:

#                 #app.logger.debug("student id:")
#                 #app.logger.debug(nb_student.id)

#                 # ceate dict for grade_data, with nested dict {student id: {score}}
#                 nb_student_and_score = {}            

#                 # Try to find the submission in the nbgrader database. If it doesn't exist, the
#                 # MissingEntry exception will be raised and we assign them a score of None.

#                 try:
#                     nb_submission = gb.find_submission(nb_assignment.name, nb_student.id)
#                 except MissingEntry:
#                     nb_student_and_score['posted_grade'] = None
#                 else:
#                     nb_student_and_score["posted_grade"] = nb_submission.score

#                 # student.id will give us student's username, ie shrakibullah. we will need to compare this to
#                 # canvas's login_id instead of user_id

#                 # TEMP HACK: e7li and shrakibullah are instructors; change their ids (after 
#                 # submission fetch above) here to students in canvas course
#                 # TODO: create submissions for canvas course students
#                 temp_nb_student_id = nb_student.id
#                 if nb_student.id == 'e7li':
#                     temp_nb_student_id = 'testacct222'
#                 if nb_student.id == 'shrakibullah':
#                     temp_nb_student_id = 'testacct333'                    

#                 # convert nbgrader username to canvas id (integer)
#                 #canvas_student_id = canvas_students[nb_student.id]
#                 canvas_student_id = canvas_students[temp_nb_student_id]
#                 nb_grade_data[canvas_student_id] = nb_student_and_score

#             # end nbgrader student loop

#             # TODO: if we have an entry in our assignment match table for this nbgrader assignment,
#             # check if its respective canvas assignment matches what came from the form.  if it doesn't,
#             # instrutor has changed the association, post an error message and bail out

#             #  if we're creating a new canvas assignment
#             try:
#                 app.logger.debug("upload submissions for existing canvas assignment;")
#                 assignment_to_upload = course.get_assignment(form_canvas_assign_id)
#                 app.logger.debug("assignment: {}".format(assignment_to_upload))
#                 canvas_assignment_id = form_canvas_assign_id     
#             except:
#                 app.logger.debug("upload submissions for non-existing canvas assignment; will be named: {}".format(form_nb_assign_name))
#                 app.logger.debug("Group: {}".format(group))  

#                 # create new assignments as published
#                 assignment_to_upload = course.create_assignment({'name':form_nb_assign_name, 'published':'true', 'assignment_group_id':group})
#                 canvas_assignment_id = assignment_to_upload.id
#                 app.logger.debug("assignment: {}".format(assignment_to_upload.name))
#                 app.logger.debug("id: {}".format(canvas_assignment_id))

#             # if (form_canvas_assign_id == 'create') :
#             #     app.logger.debug("upload submissions for non-existing canvas assignment; will be named: {}".format(form_nb_assign_name))
#             #     app.logger.debug("Group: {}".format(group))  

#             #     # create new assignments as published
#             #     assignment_to_upload = course.create_assignment({'name':form_nb_assign_name, 'published':'true', 'assignment_group_id':group})
#             #     canvas_assignment_id = assignment_to_upload.id
#             #     app.logger.debug("assignment: {}".format(assignment_to_upload))
#             #     app.logger.debug("id: {}".format(canvas_assignment_id))

#             # #  if we're uploading to an existing canvas assignment
#             # else:
#             #     # get the id of the canvas assignment for the canvas assignment name that was submitted
#             #     app.logger.debug("upload submissions for existing canvas assignment;")
#             #     assignment_to_upload = course.get_assignment(form_canvas_assign_id)
#             #     app.logger.debug("assignment: {}".format(assignment_to_upload))
#             #     canvas_assignment_id = form_canvas_assign_id           

#             # TODO: check if assignment is published, if not, publish?
#             # submit assignment
#             progress = assignment_to_upload.submissions_bulk_update(grade_data=nb_grade_data)
#             progress = progress.query()
#             session['progress_json'] = jsonpickle.encode(progress)
#             session.modified=True
#             app.logger.debug("progress url:")
#             app.logger.debug(progress.url)

#             # check if row exists in assignment match table
#             if assignment_match:
#                 app.logger.debug("Updating assignment in database")
#                 assignment_match.progress_url = progress.url
#                 assignment_match.last_updated_time = progress.updated_at
#             else:
#                 app.logger.debug("Creating new assignment in database")
#                 newMatch = AssignmentMatch(course_id=course_id, nbgrader_assign_name=form_nb_assign_name,
#                             canvas_assign_id=canvas_assignment_id, upload_progress_url=progress.url, last_updated_time=progress.updated_at)
#                 app.logger.debug(newMatch)
#                 db.session.add(newMatch)
            
#             db.session.commit()


#             # TODO: insert/update row in assignment match table
#         # end with gradebook
#     # end if POST

#     # GET (and POST): 
#     # 1) get list of canvas assignments in the "assignments group" for course via canvasapi 
#     #    wrapper version of https://canvas.instructure.com/doc/api/assignment_groups.html; use this to populate canvas assignment dropdown lists in UI
#     # 2) query nbgrader db, populate list of nbgrader assignments
#     # 3) display a UI table where each row is an nbgrader assignment
#     # 4) for each nbgrader assignment, check the sqlalchemy assignment_match table to see if there's an entry (which means it has a corresponding canvas assignment)
#     #   a) if there is: set the corresponding canvas assignment in the dropdown in the second column of page, make the other canvas assignments un-selectable.
#     #      to make dropdown items unselectable, use javascript after page onload() or similar
#     #   b) if there isn't: populate dropdown with canvas assignments that do not exist in sqlalchemy db table of matched assignments. set the dropdown to "create in canvas with same name" initially.
#     # 5) for each nbgrader assignment, indicate the status under the submit button for each assignment. 
#     #   a) if status in sqlachemy assignment_match table is complete/, show status as complete
#     #   b) if not complete: get the progress url from that db row, fetch the url using js, display the status (percent complete) below the button


#     # TODO: query sqlalchemy assignment_match table to do #4, #5 above

#     return progress
#     # return render_template('upload_grades.htm.j2', nb_assign=nb_assign, cv_assign=cv_assign, progress=progress, 
#     #     upload_progress_url=upload_progress_url,upload_progress_assignment=upload_progress_assignment)
#     # return render_template('overview.htm.j2', nb_assign=nb_assign, cv_assign=cv_assign, db_matches=db_matches,
#                         #  progress = progress)

@app.route('/reset_progress', methods=['GET', 'POST'])
def reset_progress():
    assignment = request.form.get('assignment')
    id = request.form.get('course_id')
    match = AssignmentStatus.query.filter_by(nbgrader_assign_name=assignment, course_id=int(id)).first()
    if match:
        db.session.delete(match)
        db.session.commit()
    return 'Reset'

@app.route('/get_progress', methods=['GET'])
def get_progress():

    """
    Endpoint to call from JS. queries the database for a specified assignment and returns the upload
    url for the assignment as a JSON.

    If no status is in the database, it returns null to JS.
    """

    # get assignment and course for db query
    assignment = request.args.get('assignment')
    id = request.args.get('course_id')
    
    
    if request.method == 'GET':
        status = AssignmentStatus.query.filter_by(nbgrader_assign_name=assignment, course_id=int(id)).first()

        # if match found, return db upload url as a json
        if status:
            #app.logger.debug("found match: {}, {}, {}".format(match.canvas_assign_id, assignment, id))
            #app.logger.debug("{}".format(requests.get(match.upload_progress_url).json()))
            if status.status == 'Uploaded':
                match = AssignmentMatch.query.filter_by(nbgrader_assign_name=assignment, course_id=int(id)).first()
                return json.dumps({'status': status.status, 'completion': status.completion, 'canvas_assign_id': match.canvas_assign_id})
            return json.dumps({'status': status.status, 'completion': status.completion})

        # if match not found, return null
        else:
            return json.dumps(status)

@upload_grades_blueprint.route('/upload_grades', methods=['GET', 'POST'])
@lti(error=error, request='session', role='staff', app=app)
def upload_grades(course_name="TEST_NBGRADER", lti=lti):
    #If not posting, don't upload anything
    if not request.method == "POST":
        return None

    course_id = request.form.get('course_id')
    group = request.form.get('group')
    form_canvas_assign_id = request.form.get('form_canvas_assign_id') 
    form_nb_assign_name = request.form.get('form_nb_assign_name')

    app.logger.debug("Upload Grades api_key: {}".format(session['api_key']))
    uploader = UploadGrades(course_id, group, form_canvas_assign_id, form_nb_assign_name, course_name, lti)
    uploader.init_course()
    asyncio.run(threaded_upload(uploader))
    return "upload complete"


async def threaded_upload(uploader):
    try:
        uploader.parse_form_data()
        uploader.update_database()
    except Exception as ex:
        app.logger.debug("Attempt to remove invalid status\n{}".format(ex))
        status = AssignmentStatus.query.filter_by(nbgrader_assign_name=uploader._form_nb_assign_name).first()
        status.status = 'Failed'
        status.completion = 0
        db.session.commit()

class UploadGrades:

    def __init__(self, course_id, group, form_canvas_assign_id, form_nb_assign_name, course_name, lti=lti):
       
        self._course_id = course_id
        self._group = group
        self._form_canvas_assign_id = form_canvas_assign_id
        self._form_nb_assign_name = form_nb_assign_name
        self._course_name = course_name
        self._lti = lti
        remap_dicts = { 'COGS108_SP21_A00':{'a1le':141753, 'a1ramos':141754, 'a1valdez':141755, 'a2singh':141756, 'a3ng':141757, 'a3villeg':141758, 'a5deleon':141759, 'a7torres':141760, 'a8gomez':141761, 'aadahman':141762, 'aalona':141763, 'aandreiu':141764, 'abastoms':141765, 'abchin':141766, 'abrashea':141767, 'achapman':141768, 'adimopou':141769, 'adn004':141770, 'adunning':141771, 'aecabrer':141772, 'aeofarre':141773, 'afrakes':141774, 'agapte':141775, 'agarias':141776, 'ajc075':141777, 'akhom':141778, 'aks037':141779, 'albhavsa':141780, 'alw001':141781, 'amendoza':141782, 'amharavu':141783, 'amilad':141784, 'anc232':141785, 'ando':141786, 'anh005':141787, 'anh190':141788, 'anraha':141789, 'apatankar':141790, 'apfriend':141791, 'armansou':141792, 'asaid':141793, 'astepany':141794, 'atelang':141795, 'avn001':141796, 'aziyar':141797, 'bbecze':141798, 'bborn':141799, 'bbrower':141800, 'began':141801, 'bgfang':141802, 'bphimmas':141803, 'brocchio':141804, 'brtalave':141805, 'c1flores':141806, 'c4wei':141807, 'c7tang':141808, 'cadinh':141809, 'cama':141810, 'cbvincen':141811, 'ccha':141812, 'ccl064':141813, 'cdinh':141814, 'cdm004':141815, 'cdryder':141816, 'cduong':141817, 'celbo':141818, 'cerpeldi':141819, 'chl406':141820, 'chn012':141821, 'chy002':141822, 'cmastrangelo':141823, 'crjarqui':141824, 'crsong':141825, 'csk001':141826, 'd1liu':141827, 'd3liu':141828, 'd6marque':141829, 'daminifa':141830, 'dcoy':141831, 'dec001':141832, 'dimusa':141833, 'dmerchan':141834, 'dpai':141835, 'dsc001':141836, 'e1serran':141837, 'e1tao':141838, 'e2li':141839, 'eanam':141840, 'eayala':141841, 'edinh':141842, 'eho':141843, 'ethaenra':141844, 'euaguila':141845, 'evchen':141846, 'f1zhang':141847, 'facampos':141848, 'famancil':141849, 'fayuan':141850, 'fhuynh':141851, 'fmramos':141852, 'ftjuacal':143120, 'gbulacan':143121, 'gdeandaa':143122, 'glapeyro':143123, 'gramiro':143124, 'gschwart':143125, 'gwarner':143126, 'h1chen':143127, 'h1guo':143128, 'h2yun':143129, 'hal016':143130, 'haw030':143131, 'haz001':143132, 'hcavale':143133, 'hcchang':143134, 'hechan':143135, 'hhliou':143136, 'hhwang':143137, 'hkhalil':143138, 'hlhong':143139, 'hluu':143140, 'hmw005':143141, 'hmy002':143142, 'hpanchal':143143, 'hphamtra':143144, 'hramaswamy':143145, 'huchai':143146, 'hvaid':143147, 'hwaleh':143148, 'hyick':143149, 'izendeja':143150, 'j1chahal':143151, 'j2hang':143152, 'j2vo':143153, 'j3chang':143154, 'j3mendez':143155, 'j9feng':143156, 'jal001':143157, 'jarora':143158, 'jbowman':143159, 'jcl011':143160, 'jdnguyen':143161, 'jdvachha':143162, 'jejarvis':143163, 'jfierro':143164, 'jfong':143165, 'jhan':143166, 'jhkuo':143167, 'jibian':143168, 'jil019':143169, 'jil1007':143170, 'jil1045':143171, 'jiwei':143172, 'jklee':143173, 'jmr002':143174, 'jol067':143175, 'jop010':143176, 'jot002':143177, 'jovasque':143178, 'jpusteln':143179, 'jrein':143180, 'jtdoan':143181, 'jtrang':143182, 'juc005':143183, 'jwaldorf':143184, 'jyvelasq':143185, 'k1ingham':143186, 'k5lin':143187, 'k7pham':143188, 'kbcorpuz':143189, 'kcm004':143190, 'keli':143191, 'kguruvay':143192, 'khk004':143193, 'khoshart':143194, 'kialonzo':143195, 'kisevill':143196, 'kleonmar':143197, 'klwong':143198, 'knl018':143199, 'kpream':143200, 'ksc003':143201, 'kschriek':143202, 'ksdesilv':143203, 'l1gomez':143204, 'l8smith':143205, 'ldinh':143206, 'likuwaha':143207, 'lizhao':143208, 'lnghiem':143209, 'lpellon':143210, 'lsztajnk':143211, 'm1manzan':143212, 'magondal':143213, 'mborsch':143214, 'mbussard':143215, 'mchau':143216, 'mebharga':143217, 'meschult':143218, 'mglee':143219, 'mgrenion':143220, 'mgustafs':143221, 'mik005':143222, 'mjacobo':143223, 'mleechoi':143224, 'mlyu':143225, 'mmjiang':143226, 'mml053':143227, 'mmorocho':143228, 'mottur':143229, 'mpardin':143230, 'mzhe':143231, 'mzkhan':143232, 'n2nakamu':143233, 'nagnihot':143234, 'nfithen':143235, 'nichen':143236, 'nkwong':143237, 'nmccutch':143238, 'nml015':143239, 'nqnguyen':143240, 'nsumner':143241, 'nsupangk':143242, 'ntbeileh':143243, 'omiguel':143244, 'pcarlip':143245, 'pcdoan':143246, 'pglynn':143247, 'phalder':143248, 'pinelson':143249, 'pjromero':143250, 'psyeh':143251, 'ptchang':143252, 'qramaswa':143253, 'r1li':143254, 'r1mishra':143255, 'r2vargas':143256, 'r3zhang':143257, 'raopena':143258, 'rdestaci':143259, 'rjc016':143260, 'rmanea':143261, 'rmuinos':143262, 'rosawa':143263, 'rpei':143264, 'rtvo':143265, 'rubriaco':143266, 's3kuo':143267, 's3xie':143268, 's4jin':143269, 'sasuther':143270, 'sboussar':143271, 'sebaker':143272, 'sehuh':143273, 'sgollamu':143274, 'sgomos':143275, 'shh025':143276, 'shkuk':143277, 'sie':143278, 'sjdu':143279, 'sjk002':143280, 'sjl003':143281, 'sjli':143282, 'smunukutla':143283, 'snrose':143284, 'ssantosh':143285, 'ssl104':143286, 'ssreepat':143287, 'stl005':143288, 'svanaki':143289, 'szakeri':143290, 't4ho':143291, 'taizawa':143292, 'tlu':143293, 'tmt030':143294, 'tnn050':143295, 'toh008':143296, 'tpatel':143297, 'tsidawi':143298, 'tsobocin':143299, 'ttn208':143300, 'tzfeng':143301, 'ubhattac':143302, 'ukazi':143303, 'v2le':143304, 'vkomar':143305, 'vvthai':143306, 'w3chow':143307, 'way001':143308, 'wezeng':143309, 'x1hong':143310, 'x1zhu':143311, 'x5zuo':143312, 'xih017':143313, 'xil012':143314, 'y2hua':143315, 'y3xu':143316, 'yal023':143317, 'yil031':143318, 'ymmei':143319, 'yux024':143320, 'yuz884':143321, 'z2chen':143322, 'z3xu':143323, 'z5liu':143324, 'zanguyen':143325, 'zcalini':143326, 'zhl411':143327, 'zhpi':143328, 'ziz012':143329, 'a2patel':143330, 'atsedenb':143331, 'dmngo':143332, 'ivcervan':143333, 'jwilmore':143334, 'kharris':143335, 'lgiumarr':143336, 'msinclai':143337, 'ssusanto':143338, 'yml003':143339, 'ffeng':143340, 'adrapkin':143341}, 'CSE284_SP21_A00' : {'aasehgal':141753, 'abegzati':141754, 'adilmore':141755, 'amassara':141756, 'armiano':141757, 'baxu':141758, 'bdamerac':141759, 'cguccion':141760, 'ckulkarn':141761, 'cleung':141762, 'croy':141763, 'dkoohmar':141764, 'dschenon':141765, 'dtv004':141766, 'eulee':141767, 'gul012':141768, 'hal040':141769, 'haz233':141770, 'hmummey':141771, 'hziaeija':141772, 'j1tiboch':141773, 'j7lam':141774, 'jaz001':141775, 'jiw449':141776, 'jjauregu':141777, 'jop002':141778, 'jpnguyen':141779, 'jrainton':141780, 'kpgodine':141781, 'laxu':141782, 'lbruce':141783, 'lmshea':141784, 'mcuoco':141785, 'mgaltier':141786, 'mlamkin':141787, 'ndoumbal':141788, 'ppandit':141789, 'q5yu':141790, 'r2feng':141791, 'rdevito':141792, 'rmayes':141793, 'sasafa':141794, 'snwright':141795, 'ssatyadh':141796, 'tarthur':141797, 'vktiwari':141798, 'vraghven':141799, 'vyeliset':141800, 'xid032':141801, 'yid010':141802, 'yiw078':141803, 'yul579':141804, 'z3fan':141805, 'z4ding':141806, 'zhw002':141807, 'xil104':141808}}
        #self.lookup_table = remap_dicts[course_name]
        self._setup_canvasapi_debugging()
        self._num_students = self._get_num_students()
        

    # Returns a course object corresponding to given course_id
    # TEST: param is to allow testing
    def init_course(self, flask_session = session):
        canvas_wrapper = CanvasWrapper(settings.API_URL, flask_session)
        canvas = canvas_wrapper.get_canvas()
        self._course = canvas.get_course(self._course_id)
        if self._course is None:
            raise Exception('Invalid course id')
    
    def parse_form_data(self):
        self._setup_status()
        if (self._form_canvas_assign_id == 'create'):
            app.logger.debug('get max score')
            max_score = self._get_max_score()
            app.logger.debug('create assignment')
            self.assignment_to_upload = self._create_assignment(max_score)
        else: 
            self.assignment_to_upload = self._get_assignment()

        app.logger.debug('get canvas students')
        time_start = time.time()
        canvas_students = self._get_canvas_students()
        app.logger.debug('time for get students: {}'.format(time.time()-time_start))
        app.logger.debug('get student grades')
        time_start = time.time()
        self.student_grades = self._get_student_grades(canvas_students)
        app.logger.debug('time for get grades: {}'.format(time.time()-time_start))

        

        self.canvas_assignment_id = self.assignment_to_upload.id
    
    # Submits grades to canvas, and creates/updates the AssignmentMatch database for the assignment
    def update_database(self):
        app.logger.debug('submit grades')
        time_start = time.time()
        progress = self._submit_grades()
        app.logger.debug('time for subimt: {}'.format(time.time()-time_start))
        
        assignment_match = AssignmentMatch.query.filter_by(nbgrader_assign_name=self._form_nb_assign_name, course_id=self._course_id).first()
        if assignment_match:
            app.logger.debug('update match')
            self._update_match(assignment_match, progress)
        else:
            app.logger.debug('add match')
            self._add_new_match(progress)
        self.assignment_status.status = 'Uploaded'
        self.assignment_status.completion = 100
        db.session.commit()
        return progress

    def _setup_status(self):
        self.assignment_status = AssignmentStatus.query.filter_by(course_id = self._course_id, nbgrader_assign_name = self._form_nb_assign_name).first()
        if self.assignment_status:
            self._refresh_assignment_status()
        else:
            self._create_assignment_status()

    def _create_assignment_status(self):
        self.assignment_status = AssignmentStatus(course_id=self._course_id, nbgrader_assign_name=self._form_nb_assign_name ,status = 'Initializing', completion = 0)
        db.session.add(self.assignment_status)
        db.session.commit()

    def _refresh_assignment_status(self):
        self.assignment_status.status = 'Initializing'
        self.assignment_status.completion = 0
        db.session.commit()

    #Sets up debugging for canvasapi
    def _setup_canvasapi_debugging(self):
        canvasapi_logger = logging.getLogger("canvasapi")
        canvasapi_handler = logging.StreamHandler(sys.stdout)
        canvasapi_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        canvasapi_handler.setLevel(logging.ERROR)
        canvasapi_handler.setFormatter(canvasapi_formatter)
        canvasapi_logger.addHandler(canvasapi_handler)
        canvasapi_logger.setLevel(logging.ERROR)

    #Returns a dict of student {login_id:id} corresponding to a canvas course object. Ex: {jsmith:13342}
    # The counter on this is only accurate if num_students is the number of students in the class
    def _get_canvas_students(self):
        self.assignment_status.status = 'Fetching Students'
        canvas_students = {}
        canvas_users = self._course.get_users()  
        counter=0
        for user in canvas_users:
            if hasattr(user, "login_id") and user.login_id is not None:
                canvas_students[user.login_id]=user.id  
                if counter < self._num_students:
                    counter += 1
                    self.assignment_status.completion = 10*counter/self._num_students
                    db.session.commit()
        return canvas_students
    
    #Returns a dict of {id: {'posted_grade':score}} for all students in nb gradebook
    def _get_student_grades(self, canvas_students):
        self.assignment_status.status = 'Fetching Grades'
        db.session.commit()
        with Gradebook("sqlite:////mnt/nbgrader/"+self._course_name+"/grader/gradebook.db") as gb:
            nb_assignment = gb.find_assignment(self._form_nb_assign_name)

            # TODO: can we change this to just get the students for this assignment?
            
            nb_students = gb.students            
            nb_grade_data = {}

            counter = 0            
            for nb_student in nb_students:

                nb_student_and_score = {}            

                # Try to find the submission in the nbgrader database. If it doesn't exist, the
                # MissingEntry exception will be raised and we assign them a score of None.
                
                try:
                    
                    nb_submission = gb.find_submission(nb_assignment.name, nb_student.id)
                    nb_student_and_score['posted_grade'] = nb_submission.score
                    # if max_score < nb_submission.score:
                    #     # TODO: Alert grade is higher than assignment max
                    #     # could also get high score here and then check against canvas max score later
                    #     pass
                except MissingEntry:
                    nb_student_and_score['posted_grade'] = ''

                
                    

                # student.id will give us student's username, ie shrakibullah. we will need to compare this to
                # canvas's login_id instead of user_id

                # TEMP HACK: e7li and shrakibullah are instructors; change their ids (after 
                # submission fetch above) here to students in canvas course
                # TODO: create submissions for canvas course students
                # temp_nb_student_id = nb_student.id
                # if nb_student.id == 'e7li':
                #     temp_nb_student_id = 'testacct222'
                # if nb_student.id == 'shrakibullah':
                #     temp_nb_student_id = 'testacct333'                    

                if nb_student.id == 'aa123wi21':
                    nb_student.id = 'nb2canvas_student1'
                elif nb_student.id == 'grader-test-01':
                    nb_student.id = 'nb2canvas_student2'
                elif nb_student.id == 'pjamason':
                    nb_student.id = 'nb2canvas_student3'
                # convert nbgrader username to canvas id (integer)
                # TEMP CHANGE
                canvas_student_id = canvas_students[nb_student.id]
                #canvas_student_id = self.lookup_table[nb_student.id]
                # canvas_student_id = canvas_students[temp_nb_student_id]
                nb_grade_data[canvas_student_id] = nb_student_and_score
                counter += 1
                self.assignment_status.completion = 10+45*counter/self._num_students
                db.session.commit()
            return nb_grade_data

    # gets existing canvas assignment
    def _get_assignment(self):
        app.logger.debug("upload submissions for existing canvas assignment;")
        assignment = self._course.get_assignment(self._form_canvas_assign_id)
        if assignment is None:
            raise Exception('Invalid form canvas_assign_id')
        return assignment

    def _get_max_score(self):
        with Gradebook("sqlite:////mnt/nbgrader/"+self._course_name+"/grader/gradebook.db") as gb:
            nb_assignment = gb.find_assignment(self._form_nb_assign_name)
            return nb_assignment.max_score

    def _get_num_students(self):
        with Gradebook("sqlite:////mnt/nbgrader/"+self._course_name+"/grader/gradebook.db") as gb:
            return len(gb.students)

    # create new assignments as published
    def _create_assignment(self, max_score):
        app.logger.debug("upload submissions for non-existing canvas assignment; will be named: {}".format(self._form_nb_assign_name))             
        return self._course.create_assignment({'name':self._form_nb_assign_name, 'published':'true', 'assignment_group_id':self._group, 'points_possible':max_score})
        
    

    # Updates grades for given assignment. Returns progress resulting from upload attempt.
    def _submit_grades(self):
        self.assignment_status.status = 'Uploading Grades'
        db.session.commit()
        progress = self.assignment_to_upload.submissions_bulk_update(grade_data=self.student_grades)
        try:
            session['progress_json'] = jsonpickle.encode(progress)
            session.modified = True
        except Exception:
            app.logger.debug("Error modifying session")
        app.logger.debug("progress url: {}".format(progress.url))
        counter = 0
        while not progress.workflow_state == "completed" and not progress.workflow_state == "failed":
            time.sleep(1)
            # The status bar progression is based on the assumption of linear time with 323 students taking around 75 seconds
            counter +=1
            if self.assignment_status.completion < 95:
                self.assignment_status.completion = 55 + 40*counter*4/self._num_students
                db.session.commit()
            progress = progress.query()
        return progress

    # Update existing match in database
    def _update_match(self, assignment_match, progress):
        app.logger.debug("Updating assignment in database")
        assignment_match.progress_url = progress.url
        assignment_match.last_updated_time = progress.updated_at
    
    # Creates and adds new match to database
    def _add_new_match(self, progress):
        app.logger.debug("Creating new assignment in database")
        newMatch = AssignmentMatch(course_id=self._course_id, nbgrader_assign_name=self._form_nb_assign_name,
                    canvas_assign_id=self.canvas_assignment_id, upload_progress_url=progress.url, last_updated_time=progress.updated_at)
        db.session.add(newMatch)