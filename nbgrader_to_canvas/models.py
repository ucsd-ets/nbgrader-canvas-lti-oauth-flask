from nbgrader_to_canvas import db


# DB Model
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True)
    refresh_key = db.Column(db.String(255))
    expires_in = db.Column(db.BigInteger)

    def __init__(self, user_id, refresh_key, expires_in):
        self.user_id = user_id
        self.refresh_key = refresh_key
        self.expires_in = expires_in

    def __repr__(self):
        return '<User %r>' % self.user_id
    
class Sessions(db.Model):
    #__tablename__ = table

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), unique=True)
    data = db.Column(db.LargeBinary)
    expiry = db.Column(db.DateTime)

    def __init__(self, session_id, data, expiry):
        self.session_id = session_id
        self.data = data
        self.expiry = expiry

class AssignmentMatch(db.Model):
    #__tablename__ = table

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer)
    nbgrader_assign_name = db.Column(db.String(255))
    canvas_assign_id = db.Column(db.Integer, unique=True)
    upload_progress_url = db.Column(db.String(255))
    last_updated_time = db.Column(db.String(255))

    def __init__(self, course_id, nbgrader_assign_name, canvas_assign_id, upload_progress_url, last_updated_time):
        self.course_id = course_id
        self.nbgrader_assign_name = nbgrader_assign_name
        self.canvas_assign_id = canvas_assign_id
        self.upload_progress_url = upload_progress_url
        self.last_updated_time = last_updated_time
