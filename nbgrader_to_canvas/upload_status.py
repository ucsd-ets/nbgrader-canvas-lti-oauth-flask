from types import GetSetDescriptorType
from flask import Blueprint, render_template, session, request
from pylti.flask import lti

from .utils import error
from . import app
from . import settings
from nbgrader.api import Gradebook, MissingEntry

import json
import logging
import sys
import jsonpickle
upload_status_blueprint = Blueprint('upload_status', __name__)

# Web Views / Routes
@upload_status_blueprint.route('/upload_status', methods=['GET', 'POST'])
@lti(error=error, request='session', role='staff', app=app)
def upload_status(lti=lti):

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

    args = request.args.to_dict()

    course_id = session['course_id']

    # initialize a new canvasapi Canvas object
    #canvas = get_canvas()

    # canvasapi debugging info https://github.com/ucfopen/canvasapi/blob/master/docs/debugging.rst
    logger = logging.getLogger("canvasapi")
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    handler.setLevel(logging.ERROR)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)

    progress = jsonpickle.decode(session['progress_json'])
    progress = progress.query()

    return render_template('upload_status.htm.j2', progress=progress, BASE_URL=settings.BASE_URL)
