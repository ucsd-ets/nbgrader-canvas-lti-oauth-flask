import os

# API url and LTI key/secret
BASE_URL = 'https://ucsd.test.instructure.com/'
API_URL = 'https://ucsd.test.instructure.com/'
LTI_CONSUMER_KEY = os.getenv('LTI_CONSUMER_KEY')
LTI_SHARED_SECRET = os.getenv('LTI_SHARED_SECRET')

# generate a secret key with os.urandom(24)
secret_key = 'SfHNb6S3uwUmg68VrZF67dZErsR/WGNg'

# logs
LOG_FILE = 'error.log'
LOG_FORMAT = '%(asctime)s [%(levelname)s] {%(filename)s:%(lineno)d} %(message)s'
LOG_LEVEL = 'INFO'
LOG_MAX_BYTES = 1024 * 1024 * 5  # 5 MB
LOG_BACKUP_COUNT = 1

# $oauth2_id: The Client_ID Instructure gives you
# $oauth2_key: The Secret Instructure gives you
# $oauth2_uri: The "Oauth2 Redirect URI" you provided instructure.
# $oauth2_scopes: The scopes to request for use by this application.

if os.path.isfile('/app/selenium/on'):
    oauth2_id = os.getenv('SELENIUM_OAUTH2_ID')
    oauth2_key = os.getenv('SELENIUM_OAUTH2_KEY')
    oauth2_uri = os.getenv('SELENIUM_OAUTH2_URI')

else:
    oauth2_id = os.getenv('OAUTH2_ID')
    oauth2_key = os.getenv('OAUTH2_KEY')
    oauth2_uri = os.getenv('OAUTH2_URI')

oauth2_scopes = " ".join([
    # Uncomment the following line and add your desired scopes to enable token scoping:
    # "url:GET|/api/v1/users/:user_id/profile",
])

# config object settings
configClass = 'nbgrader_to_canvas.config.DevelopmentConfig'

DATABASE_URIS = {
    'DevelopmentConfig': 'postgresql://dev:mypassword@postgres/test',
    'Config': 'postgresql://dev:mypassword@postgres/test',
    'BaseConfig': 'postgresql://dev:mypassword@postgres/test',
    'TestingConfig': 'postgresql://dev:mypassword@postgres/test'
}

PYLTI_CONFIG = {
    'consumers': {
        LTI_CONSUMER_KEY: {
            "secret": LTI_SHARED_SECRET
        }
    },
    'roles': {
        'admin': ['Administrator', 'urn:lti:instrole:ims/lis/Administrator'],
        'student': ['Student', 'urn:lti:instrole:ims/lis/Student']
    }
}
