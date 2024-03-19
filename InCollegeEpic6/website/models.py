from . import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    accountName = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    fname = db.Column(db.String(150))
    lname = db.Column(db.String(150))
    title = db.Column(db.String(150))
    major = db.Column(db.String(150), default="")
    university = db.Column(db.String(150), default="")
    about = db.Column(db.String(2000))
    hasProfile = db.Column(db.Boolean, default=False)
    hasInfo = db.Column(db.Boolean, default=False)
    hasExp = db.Column(db.Boolean, default=True)
    hasEdu = db.Column(db.Boolean, default=False)
    email_option = db.Column(db.Boolean, default=True)
    sms_option = db.Column(db.Boolean, default=True)
    advertising_option = db.Column(db.Boolean, default=True)
    language = db.Column(db.String(150), default='English')
    notified_job_deletion = db.Column(db.Boolean, default=False, nullable=False)
    # Jobs posted by the user
    jobs = db.relationship('Job', backref='poster', lazy=True, cascade="all, delete")
    

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    description = db.Column(db.String(150))
    employer = db.Column(db.String(150))
    location = db.Column(db.String(150))
    salary = db.Column(db.Integer)
    accountName = db.Column(db.String(150), db.ForeignKey('user.accountName', ondelete='CASCADE'))
    # Explicitly defining relationships
    applications = db.relationship('JobApplication', back_populates='job', cascade="all, delete-orphan")
    saved_by_users = db.relationship('SavedJob', back_populates='job', cascade="all, delete-orphan")

# create friend table
class Friend(db.Model):
    # user_id and friend_id are primary keys together. Both are foreign keys to the User table
    user = db.Column(db.String(150), db.ForeignKey('user.accountName', ondelete='CASCADE'), primary_key=True)
    friend = db.Column(db.String(150), db.ForeignKey('user.accountName', ondelete='CASCADE'), primary_key=True)

    # a column to store the status of the friend request. 3 statuses: pending, accepted, default
    status = db.Column(db.String(150), default='default')


class Experience(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(150), db.ForeignKey('user.accountName', ondelete='CASCADE'))
    jobTitle = db.Column(db.String(150))
    jobEmployer = db.Column(db.String(150))
    dateStart = db.Column(db.String(150))
    dateEnd = db.Column(db.String(150))
    jobLocation = db.Column(db.String(150))
    jobDescription = db.Column(db.String(2000))

class Education(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(150), db.ForeignKey('user.accountName', ondelete='CASCADE'))
    schoolName = db.Column(db.String(150))
    degree = db.Column(db.String(150))
    years = db.Column(db.String(150))

class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id', ondelete='CASCADE'), nullable=False)
    graduation_date = db.Column(db.String(10))
    start_date = db.Column(db.String(10))
    cover_letter = db.Column(db.String(2000))
    # Setting up back_populates for explicit two-way relationships
    user = db.relationship('User', back_populates='applications')
    job = db.relationship('Job', back_populates='applications')
    
class SavedJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id', ondelete='CASCADE'), nullable=False)
    # Setting up back_populates for explicit two-way relationships
    user = db.relationship('User', back_populates='saved_jobs')
    job = db.relationship('Job', back_populates='saved_by_users')

# Update the User model to include reverse relationships for JobApplication and SavedJob
User.applications = db.relationship('JobApplication', back_populates='user', lazy='dynamic')
User.saved_jobs = db.relationship('SavedJob', back_populates='user', lazy='dynamic')
