from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(10000), unique=True) # path to actual .pdf file
    file_markup = db.Column(db.String(100000)) # markup of the file
    filename = db.Column(db.String(10000)) # actual filename shown on website
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000))
    table = db.Column(db.String(100000)) # serialized json table file
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    files = db.relationship('File')

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    projects = db.relationship('Project')
