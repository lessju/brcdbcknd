import uuid

from flask_login import UserMixin

from backend.app import db


class User(UserMixin, db.Model):
    """ Class representing a user """
    __tablename__ = "user_table"

    id = db.Column(db.Integer, default=lambda: uuid.uuid4().int >> (128 - 32), primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    recycled_containers = db.Column(db.Integer, default=0)
    balance = db.Column(db.Float(), default=0)
    session_start_time = db.Column(db.DateTime, unique=False, server_default=db.func.now())
    session_end_time = db.Column(db.DateTime, unique=False, server_default=db.func.now())


class RecycledContainer(db.Model):
    """ Class representing a recycled container """
    id = db.Column(db.Integer, primary_key=True)
    container_id = db.Column(db.Integer, unique=False)
    user_id = db.Column(db.Integer, unique=False)
    accepted = db.Column(db.Boolean, default=True)
    timestamp = db.Column(db.DateTime, unique=False)


class RecyclingBin(db.Model):
    """ Class representing a recycling bin"""
    __tablename__ = "bin_table"

    id = db.Column(db.Integer, primary_key=True)
    qrcode = db.Column(db.Integer, unique=True)
    online = db.Column(db.Boolean, default=False)
    available = db.Column(db.Boolean, default=False)
    created_time = db.Column(db.DateTime, server_default=db.func.now())
    modified_time = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())


class RecyclableContainer(db.Model):
    """ Class representing a recyclable container """
    __tablename__ = "container_table"

    id = db.Column(db.Integer, primary_key=True)
    barcode = db.Column(db.String(100), unique=True)
    label = db.Column(db.String(100), default="Container label")
    weight = db.Column(db.Float(), default=100)
    monetary_value = db.Column(db.Float(), default=10)