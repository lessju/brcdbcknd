from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from backend.models import User
from backend.app import db

auth = Blueprint('auth', __name__)


@auth.route('/login')
def login():
    return render_template('login.html')


@auth.route('/login', methods=['POST'])
def login_post():
    # Get login information
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    # Check if the user actually exists
    user = User.query.filter_by(email=email).first()

    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        # If the user doesn't exist or password is wrong, reload the page
        return redirect(url_for('auth.login'))

    # If the above check passes, credentials are right
    login_user(user, remember=remember)

    return redirect(url_for('main.index'))


@auth.route('/signup')
def signup():
    return render_template('signup.html')


@auth.route('/signup', methods=['POST'])
def signup_post():
    # Code to validate and add user to database
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    # Check if specified email already exists
    if User.query.filter_by(email=email).first():
        flash('Email address already exists!')
        return redirect(url_for('auth.signup'))

    # Create a new user with the form data. Hash password
    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))

    # Add new user to database
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('auth.login'))


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
