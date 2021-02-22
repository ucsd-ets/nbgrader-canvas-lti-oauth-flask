from flask import Blueprint, jsonify
import time

healthz_blueprint = Blueprint('healthz', __name__)

START_TIME = time.time()

@healthz_blueprint.route('/healthz')
def health():
    """Check the health of the app by outputting the uptime

    Returns:
        string: json data referencing the apps health
    """
    uptime_seconds = time.time() - START_TIME
    return jsonify({
        'uptime': round(uptime_seconds, 0),
        'message': 'ok'
    })