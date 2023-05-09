import datetime
import json

from flask_login import login_required, current_user
from flask import Blueprint, render_template, request
from apscheduler.schedulers.background import BackgroundScheduler

from backend.models import RecyclingBin, RecyclableContainer, User
from backend.app import db

main = Blueprint('main', __name__)

# User to bin association
user_bin_association = {}

# Generic 200 HTTP reply
reply_200 = json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


# --------- Background services ----------
def update_bin_state():
    """ Function called by scheduler that check the last modified time of recycling bins """
    for recycling_bin in RecyclingBin.query.all():
        if (datetime.datetime.now() - recycling_bin.modified_time) > 300:
            print("Bin not online anymore")
            RecyclingBin.available = False
            RecyclingBin.online = False
            db.session.commit()
    return


# Every minute update the status of recycling bins
sched = BackgroundScheduler(daemon=True)
sched.add_job(update_bin_state, 'interval', minutes=1)
sched.start()


# --------- Front end functionality ----------
@main.route('/')
def index():
    return render_template('index.html')


@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)


# ---------- User Backend functionality -----------
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
    reply['bin_available'] = recycling_bin.bin_available
    if not reply['bin_online'] and reply['bin_available']:
        return json.dumps(reply), 200, {'ContentType': 'application/json'}

    # If bin is already associated with a user, replace mapping (assume previous user has not stopped session)
    for k, v in user_bin_association.items():
        if v == recycling_bin.id:
            user_bin_association.pop(k)
            break

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
@main.route('/bin_keepalive/<bin_id>')
def bin_keepalive(bin_id):
    """ Period keep alive sent by a recycling bin"""

    # If the recycling bin is not in database, assume that it is a new bin and add it
    recycling_bin = RecyclingBin.query.filter_by(id=bin_id).first()
    if not recycling_bin:
        recycling_bin = RecyclingBin(id=bin_id, qrcode=bin_id, online=True)
        db.session.add(recycling_bin)
        db.session.commit()

    # Otherwise, set it to online (even if it is already online, this will force an update
    # to the modified time
    else:
        recycling_bin.online = True

    # Commit changes
    db.session.commit()

    # Return success
    return reply_200


@main.route("/scanned_container/", methods=['POST'])
def scanned_barcode():
    """ A recycling container has scanned a barcode """
    # Get post body contents
    bin_id = request.json['bin_id']
    barcode = request.json['barcode']

    # Check if barcode is valid
    container = RecyclableContainer.query.filter_by(barcode=barcode).first()
    if not container:
        return json.dumps({'success': False}), 200, {'ContentType': 'application/json'}

    # Get associated user
    user_id = -1
    for k, v in user_bin_association.items():
        if v == bin_id:
            user_id = k
            break

    # If user_id is still -1, then there is no user associated with the bin.
    # The bottle should still be recycled but no monetary value is provided to any user
    if user_id != -1:
        user = User.query.filter_by(id=user_id).first()
        user.recycled_containers += 1
        user.balance += container.monetary_value
        db.session.commit()

    # Return success
    return reply_200
