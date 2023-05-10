import datetime
import json

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from backend.app import db
from backend.models import RecyclingBin, RecyclableContainer, User

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
    return render_template('profile.html', name=current_user.name)


# ---------- User Backend functionality -----------

@main.route("/stop_session")
@login_required
def stop_session():
    """ Stop user session with current bin """

    # Mark bin as available
    recycling_bin = user_bin_association[current_user.id]
    recycling_bin = RecyclingBin.query.filter_by(id=recycling_bin).first()
    recycling_bin.available = True
    db.session.commit()

    return reply_200


@main.route("/scan_bin_qrcode", methods=['POST'])
@login_required
def scan_bin_qrcode():
    """ User has scanned a bin qrcode. Check whether qrcode exists, bin is available and if so
        associate bin to user """

    reply = {'bin_online': False,
             'bin_available': False}

    # Get qrcode from request body
    qrcode = request.json['qrcode']

    # Check if qrcode exists
    recycling_bin = RecyclingBin.query.filter_by(qrcode=qrcode).first()
    if not recycling_bin:
        return json.dumps(reply), 200, {'ContentType': 'application/json'}

    # If it exists, check that the bin is online and available
    reply['bin_online'] = recycling_bin.online
    reply['bin_available'] = recycling_bin.available
    if not reply['bin_online'] and reply['bin_available']:
        return json.dumps(reply), 200, {'ContentType': 'application/json'}

    # If bin is already associated with a user, replace mapping (assume previous user has not stopped session)
    user_id = get_user_id_from_bin(recycling_bin.id)
    if user_id != -1:
        user_bin_association.pop(user_id)

    # User can use recycling bin. Associate user with bin
    user_bin_association[current_user.id] = recycling_bin.id

    # Mark bin as unavailable
    recycling_bin.available = False
    db.session.commit()

    # Return success
    return json.dumps(reply), 200, {'ContentType': 'application/json'}


@main.route("/end_bin_session")
@login_required
def end_bin_session():
    """ User has ended a session with the recycling bin"""

    # Mark bin as available
    recycling_bin = RecyclingBin.query.filter_by(id=user_bin_association[current_user.id]).first()
    recycling_bin.available = True
    db.session.commit()

    # Remove user-bin mapping
    if current_user.id in user_bin_association.keys():
        user_bin_association.pop(current_user.id)

    return reply_200


# ---------- Bin Backend functionality -----------
@main.route('/bin_keepalive', methods=['POST'])
def bin_keepalive():
    """ Period keep alive sent by a recycling bin"""

    bin_id = request.json['bin_id']
    print(f"Received keepalive from {bin_id}")

    # If the recycling bin is not in database, assume that it is a new bin and add it
    recycling_bin = RecyclingBin.query.filter_by(id=bin_id).first()
    if not recycling_bin:
        recycling_bin = RecyclingBin(id=bin_id, qrcode=bin_id, online=True, available=True)
        db.session.add(recycling_bin)
        db.session.commit()
        print(f"Added {bin_id} to database")

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


@main.route("/check_user_request", methods=['POST'])
def check_user_request():
    """ Check whether a user has request use for the specified bin"""
    bin_id = request.json['bin_id']

    print(f"Bin {bin_id} checked for user request")

    # Get associated user, if any
    user_id = get_user_id_from_bin(bin_id)

    # if user_id is still -1 return
    if user_id == -1:
        return json.dumps({'requested': False}), 200, {'ContentType': 'application/json'}

    # Otherwise, mark bin as not available
    recycling_bin = RecyclingBin.query.filter_by(id=bin_id).first()
    recycling_bin.available = False
    db.session.commit()

    # Return reply
    return json.dumps({'requested': True}), 200, {'ContentType': 'application/json'}


@main.route("/verify_barcode/", methods=['POST'])
def verify_barcode():
    """ A recycling container has scanned a barcode """
    # Get post body contents
    barcode = request.json['barcode']

    # Check if barcode is valid
    container = RecyclableContainer.query.filter_by(barcode=barcode).first()
    if not container:
        return json.dumps({'success': False}), 200, {'ContentType': 'application/json'}

    # Return success
    return reply_200


@main.route("/confirm_barcode/", methods=['POST'])
def confirm_barcode():
    # Get post body contents
    bin_id = request.json['bin_id']
    barcode = request.json['barcode']

    # Check if barcode is valid
    container = RecyclableContainer.query.filter_by(barcode=barcode).first()
    if not container:
        return json.dumps({'success': False}), 200, {'ContentType': 'application/json'}

    # Get associated user
    user_id = get_user_id_from_bin(bin_id)

    # If user_id is still -1, then there is no user associated with the bin.
    # The bottle should still be recycled but no monetary value is provided to any user
    if user_id != -1:
        user = User.query.filter_by(id=user_id).first()
        user.recycled_containers = User.recycled_containers + 1
        user.balance = User.balance + container.monetary_value
        db.session.commit()

    # Return success
    return reply_200