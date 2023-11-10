import datetime
import json

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from backend.app import db
from backend.models import RecyclingBin, RecyclableContainer, User, RecycledContainer

main = Blueprint('main', __name__)

# User to bin association
user_bin_association = {}

# Generic 200 HTTP reply
reply_200 = json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


def get_user_id_from_bin(bin_id):
    """ Return the user ID if a user is associated with the bin, -1 otherwise"""
    for k, v in user_bin_association.items():
        if v == bin_id:
            return k
    return -1


# --------- Front end functionality ----------
@main.route('/')
def index():
    return render_template('index.html')


@main.route('/profile')
@login_required
def profile():
    """ Generate the profile page """
    # Get list of recycled containers
    user = User.query.filter_by(id=current_user.id).first()

    # Get list of recycled containers with associated timestamps
    containers = RecycledContainer.query.filter_by(user_id=current_user.id).all()
    recycled_containers = []
    for row in containers:
        cnt = RecyclableContainer.query.filter_by(id=row.container_id).first()
        recycled_containers.append((row.timestamp, cnt.label))

    return render_template('profile.html',
                           balance=round(user.balance, 2),
                           recycled_containers=recycled_containers)


@main.route("/clear_history")
@login_required
def clear_history():
    # Get list of recycled containers
    user = User.query.filter_by(id=current_user.id).first()

    # Get list of recycled containers
    RecycledContainer.query.filter_by(user_id=current_user.id).delete()

    # Commit changes
    db.session.commit()

    # Re-render profile page
    return profile()

# ---------- User Backend functionality -----------


@main.route("/stop_session")
@login_required
def stop_session():
    """ Stop user session with current bin """

    # Mark bin as available
    recycling_bin = user_bin_association[current_user.id]
    recycling_bin = RecyclingBin.query.filter_by(id=recycling_bin).first()
    recycling_bin.available = True
    del user_bin_association[current_user.id]
    db.session.commit()

    return reply_200


# ---------- Bin Backend functionality -----------
@main.route('/bin_keepalive', methods=['POST'])
def bin_keepalive():
    """ Period keep alive sent by a recycling bin"""

    bin_id = request.json['bin_id']

    # If the recycling bin is not in database, assume that it is a new bin and add it
    recycling_bin = RecyclingBin.query.filter_by(id=bin_id).first()
    if not recycling_bin:
        recycling_bin = RecyclingBin(id=bin_id, qrcode=bin_id, online=True, available=True)
        db.session.add(recycling_bin)
        db.session.commit()

    # Otherwise, set it to online, mark bin as available if not user is associated
    # with it, and force-update modified time
    else:
        recycling_bin.online = True
        if get_user_id_from_bin(recycling_bin.id) == -1:
            recycling_bin.available = True
        recycling_bin.modified_time = datetime.datetime.utcnow()

    # Commit changes
    db.session.commit()

    # Return success
    return reply_200


@main.route("/confirm_user", methods=['POST'])
def confirm_user():
    """ Check whether scanned barcode is a valid user """
    user_id = request.json['user_id']

    # Check whether user exists
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return json.dumps({'success': False}), 200, {'ContentType': 'application/json'}

    # If user is confirmed, start session
    user.session_start_time = datetime.datetime.now()
    db.session.commit()

    return reply_200


@main.route("/end_user_session", methods=['POST'])
def end_user_session():
    """ End the current user session with the bin """
    user_id = request.json['user_id']

    # Check whether user exists
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return json.dumps({'success': False}), 200, {'ContentType': 'application/json'}

    # Set session end time for user
    user.session_end_time = datetime.datetime.now()

    # Commit changes
    db.session.commit()

    return reply_200


@main.route("/verify_barcode/", methods=['POST'])
def verify_barcode():
    """ A recycling container has scanned a barcode """
    # Get post body contents
    barcode = request.json['barcode']

    # Check if barcode is valid
    container = RecyclableContainer.query.filter_by(barcode=barcode).first()
    if not container:
        return json.dumps({'success': False}), 200, {'ContentType': 'application/json'}

    # Otherwise, return success and the container's weight
    return json.dumps({'success': True, 'weight': container.weight}), 200, {'ContentType': 'application/json'}


@main.route("/confirm_barcode/", methods=['POST'])
def confirm_barcode():
    # Get post body contents
    user_id = request.json['user_id']
    barcode = request.json['barcode']

    # Get container
    container = RecyclableContainer.query.filter_by(barcode=barcode).first()

    # Get user
    user = User.query.filter_by(id=user_id).first()

    # Keep record of recycled containers
    recycled_container = RecycledContainer(user_id=user.id, container_id=container.id, timestamp=datetime.datetime.now())
    db.session.add(recycled_container)

    # Provide compensation to user
    user.recycled_containers = User.recycled_containers + 1
    user.balance = User.balance + container.monetary_value

    # Commit changes to database
    print("Added", recycled_container.timestamp)
    db.session.commit()

    return reply_200


@main.route("/reject_barcode", methods=['POST'])
def reject_barcode():
    # Get post body contents
    user_id = request.json['user_id']
    barcode = request.json['barcode']

    # Get user
    user = User.query.filter_by(id=user_id).first()

    # Keep record of recycled containers
    recycled_container = RecycledContainer(user_id=user_id, container_id=barcode,
                                           accepted=False, timestamp=datetime.datetime.now())
    db.session.add(recycled_container)

    # Commit changes to database
    db.session.commit()

    return reply_200


@main.route("/get_session_bottles", methods=['POST'])
def get_session_bottles():
    # Get post body contents
    user_id = request.json['user_id']

    # Get list of recycled containers
    user = User.query.filter_by(id=user_id).first()

    end_time = datetime.datetime.now()
    if user.session_end_time < user.session_start_time:
        end_time = user.session_end_time
    print("Between", user.session_start_time, end_time)

    # Get list of recycled containers with associated timestamps
    containers = RecycledContainer.query.filter(RecycledContainer.user_id == user_id,
                                                RecycledContainer.timestamp <= end_time,
                                                RecycledContainer.timestamp >= user.session_start_time).all()
    recycled_containers = []
    for row in containers:
        cnt = RecyclableContainer.query.filter_by(id=row.container_id).first()
        if cnt is None:
            recycled_containers.append(
                (row.timestamp.strftime("%Y-%m-%d %H:%M:%S"), row.container_id, 0, row.accepted))
        else:
            recycled_containers.append((row.timestamp.strftime("%Y-%m-%d %H:%M:%S"), cnt.label, cnt.monetary_value, row.accepted))
    print(recycled_containers)

    return json.dumps({'success': True, 'bottles': recycled_containers}), 200, {'ContentType': 'application/json'}