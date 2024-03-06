from . import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    accountName = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    fname = db.Column(db.String(150))
    lname = db.Column(db.String(150))
    job = db.relationship('Job', backref='user')
    title = db.Column(db.String(150))
    major = db.Column(db.String(150), default="")
    university = db.Column(db.String(150), default="")
    about = db.Column(db.String(2000))
    hasProfile = db.Column(db.Boolean, default=False) # set True when info and edu are saved - profile is finished
    hasInfo = db.Column(db.Boolean, default=False) # Set True when title, major, university, about have been saved
    hasExp = db.Column(db.Boolean, default=True) # Set true when all forms for the experience have been filled out completely, or no experience has been added
    hasEdu = db.Column(db.Boolean, default=False) # set True when all education values have been saved



    # Newly added by Toan
    email_option = db.Column(db.Boolean, default=True)
    sms_option = db.Column(db.Boolean, default=True)
    advertising_option = db.Column(db.Boolean, default=True)
    language = db.Column(db.String(150), default='English')
    

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    description = db.Column(db.String(150))
    employer = db.Column(db.String(150))
    location = db.Column(db.String(150))
    salary = db.Column(db.Integer)
    accountName = db.Column(db.String(150), db.ForeignKey('user.accountName'))  # Corrected to String to match the User's accountName


# create friend table
class Friend(db.Model):
    # user_id and friend_id are primary keys together. Both are foreign keys to the User table
    user = db.Column(db.String(150), db.ForeignKey('user.accountName'), primary_key=True)
    friend = db.Column(db.String(150), db.ForeignKey('user.accountName'), primary_key=True)

    # a column to store the status of the friend request. 3 statuses: pending, accepted, default
    status = db.Column(db.String(150), default='default')


class Experience(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(150), db.ForeignKey('user.accountName'))
    jobTitle = db.Column(db.String(150))
    jobEmployer = db.Column(db.String(150))
    dateStart = db.Column(db.String(150))
    dateEnd = db.Column(db.String(150))
    jobLocation = db.Column(db.String(150))
    jobDescription = db.Column(db.String(2000))

class Education(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(150), db.ForeignKey('user.accountName'))
    schoolName = db.Column(db.String(150))
    degree = db.Column(db.String(150))
    years = db.Column(db.String(150))
