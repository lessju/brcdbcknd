from flask_login import UserMixin
from backend.app import db


class User(UserMixin, db.Model):
    """ Class representing a user """
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    balance = db.Column(db.Float(), default=0)


class RecyclingBin(db.Model):
    """ Class representing a recycling bin"""
    id = db.Column(db.Integer, primary_key=True)
    qrcode = db.Column(db.Integer, unique=True)


class Container(db.Model):
    """ Class representing a recyclable container """
    id = db.Column(db.Integer, primary_key=True)
    barcode = db.Column(db.String(100), unique=True)

    # Monetary value gained when recycling container
    monetary_value = db.Column(db.Float(), default=10)