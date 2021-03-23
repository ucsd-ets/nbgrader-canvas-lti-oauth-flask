import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_sqlalchemy import SQLAlchemy
from prometheus_flask_exporter import PrometheusMetrics
from datetime import timedelta
from flask_session import Session, SqlAlchemySessionInterface

from . import settings

__version__ = '0.0.1'

# initialize the app
app = Flask(__name__, template_folder='./templates')

# filesystem session interface, see https://github.com/fengsp/flask-session/blob/master/docs/index.rst#built-in-session-interfaces
#app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=5)
#app.config['SESSION_FILE_DIR'] = '/tmp'
#app.config['SESSION_PERMANENT'] = True
# The maximum number of items the session stores 
# before it starts deleting some, default 500
#app.config['SESSION_FILE_THRESHOLD'] = 100  

# db session interface instead of filesystem due to user tokens stored in db Users table
# see sqlalchemy code after init_app below too
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SESSION_TYPE'] = 'sqlalchemy'

app.secret_key = settings.secret_key
app.config.from_object(settings.configClass)

#app.config['SECRET_KEY'] = config.SECRET_KEY

# initialize session instance with app
sess = Session()
sess.init_app(app)


# add middleware
app.wsgi_app = ProxyFix(app.wsgi_app)


#
# intialize all other modules here due to circ. import errors
#

# initialize db
db = SQLAlchemy(app)

# below may not be required; we create sessions table manually in models.py
# https://stackoverflow.com/questions/45887266/flask-session-how-to-create-the-session-table?noredirect=1&lq=1
#app.config['SESSION_SQLALCHEMY'] = os.getenv('DATABASE_URI')
app.config['SESSION_SQLALCHEMY'] = db
app.config['SESSION_SQLALCHEMY_TABLE'] = 'sessions'
#SqlAlchemySessionInterface(app, db, "sessions", "sess_")

from . import models
db.create_all()

# routes
from .healthz import healthz_blueprint
from .launch import launch_blueprint
from .oauthlogin import oauth_login_blueprint
from .xml import xml_blueprint
from .index import index_blueprint
from .upload_grades import upload_grades_blueprint
from .upload_status import upload_status_blueprint

app.register_blueprint(healthz_blueprint)
app.register_blueprint(oauth_login_blueprint)
app.register_blueprint(xml_blueprint)
app.register_blueprint(index_blueprint)
app.register_blueprint(launch_blueprint)
app.register_blueprint(upload_grades_blueprint)
app.register_blueprint(upload_status_blueprint)

# setup Prometheus route at /metrics
metrics = PrometheusMetrics(app, path='/metrics')
metrics.info('nbgrader_to_canvas_info', 'app info', version=__version__)
