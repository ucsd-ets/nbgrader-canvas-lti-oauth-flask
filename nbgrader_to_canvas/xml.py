from flask import Blueprint, Response, render_template

from . import app
from .utils import return_error

xml_blueprint = Blueprint('xml', __name__)

# XML
@xml_blueprint.route("/xml", methods=['GET'], strict_slashes=False)
def xml():
    """
    Returns the lti.xml file for the app.
    XML can be built at https://www.eduappcenter.com/
    """
    try:
        return Response(
            render_template('lti.xml.j2'),
            mimetype='application/xml'
        )
    except Exception as e:
        app.logger.error(e)
        import os
        app.logger.error(os.getcwd())
        app.logger.error("No XML file.")
        msg = (
            'No XML file. Please refresh and try again. '
            'If this error persists, please contact support.'
        )
        return return_error(msg)