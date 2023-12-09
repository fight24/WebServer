
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum as UserEnum
from flask_login import UserMixin
db = SQLAlchemy()

device_user_association = db.Table(
    'device_user_association',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('device_id', db.Integer, db.ForeignKey('devices.id'))
)
device_image_association = db.Table(
    'device_image_association',
    db.Column('device_id',db.Integer,db.ForeignKey('devices.id')),
    db.Column('Image_id',db.Integer,db.ForeignKey('image.id'))
)
user_image_association = db.Table(
    'user_image_association',
    db.Column('user_id',db.Integer,db.ForeignKey('users.id')),
    db.Column('Image_id',db.Integer,db.ForeignKey('image.id'))
)
class UserRole(UserEnum):
    ADMIN = 1
    USER = 2
class User(db.Model,UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    img_user = db.Column(db.String(120))
    devices = db.relationship('Device', secondary=device_user_association, back_populates='users')
    images = db.relationship('Image',secondary=user_image_association,back_populates='users')
    user_role = db.Column(db.Enum(UserRole),default=UserRole.USER)
    def __init__(self, username, email,password,img_user):
        self.username = username
        self.email = email
        self.password = password
        self.img_user = img_user
    def __init__(self,username,email,password):
        self.username = username
        self.email = email
        self.password = password
    def set_username(self,username):
        self.username = username
    def get_username(self):
        return self.username
    def get_email(self):
        return self.email
    def set_email(self, email):
        self.email = email

class Device(db.Model):
    __tablename__ = 'devices'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    code = db.Column(db.String(120), unique=True, nullable=False)
    type = db.Column(db.String(50))
    is_warning = db.Column(db.Boolean,default = False)
    is_status = db.Column(db.Boolean,default = False)
    image_name = db.Column(db.String(120))
    distance = db.Column(db.Float)
    def __init__(self,name,code,type,is_warning,is_status):
        self.name = name
        self.code = code
        self.type = type
        self.is_warning = is_warning
        self.is_status = is_status
        
    users = db.relationship('User', secondary=device_user_association, back_populates='devices')
    property = db.relationship('Property', backref='device', lazy='dynamic')
    images = db.relationship('Image',secondary=device_image_association,back_populates='devices')
class Property(db.Model):
    __tablename__ = 'properties'
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(120))
    message = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'))
class Image(db.Model):
    __tablename__ = 'image'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120),primary_key = True)
    devices = db.relationship('Device',secondary=device_image_association,back_populates='images')
    users = db.relationship('User',secondary=user_image_association,back_populates='images')
class Token(db.Model):
    __tablename__ = 'tokens'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    token_value = db.Column(db.String(255), unique=True, nullable=False)
    user = db.relationship('User', backref='token', uselist=False)