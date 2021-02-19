from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_sqlalchemy import SQLAlchemy
from prometheus_flask_exporter import PrometheusMetrics

from . import settings

__version__ = '0.0.1'

# initialize the app
app = Flask(__name__, template_folder='./templates')
app.secret_key = settings.secret_key
app.config.from_object(settings.configClass)

# add middleware
app.wsgi_app = ProxyFix(app.wsgi_app)

#
# intialize all other modules here due to circ. import errors
#

# initialize db
db = SQLAlchemy(app)
from . import models
db.create_all()

# routes
from .healthz import healthz_blueprint
from .launch import launch_blueprint
from .oauthlogin import oauth_login_blueprint
from .xml import xml_blueprint
from .index import index_blueprint

app.register_blueprint(healthz_blueprint)
app.register_blueprint(oauth_login_blueprint)
app.register_blueprint(xml_blueprint)
app.register_blueprint(index_blueprint)
app.register_blueprint(launch_blueprint)

# setup Prometheus route at /metrics
metrics = PrometheusMetrics(app)
metrics.info('nbgrader_to_canvas_info', 'nbgrader_to_canvas info', version=__version__)