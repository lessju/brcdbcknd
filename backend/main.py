from flask_login import login_required, current_user

from backend.database.bin import Bin

from flask import Blueprint, render_template

main = Blueprint('main', __name__)

# Load barcode database
with open("backend/database/barcodes.txt") as f:
    barcodes = [int(x) for x in f.readlines()]

# Load bins
with open("backend/database/bins.txt") as f:
    bins = {bin_id.strip(): Bin(bin_id.strip()) for bin_id in f.readlines()}


# --------- Main Page ----------
@main.route('/')
def index():
    return render_template('index.html')


# --------- User Management ----------
@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)


# ---------- Backend functionality -----------
@main.route('/mark_bin_available/<bin_id>')
def mark_bin_available(bin_id):
    if bin_id in bins.keys():
        bins[bin_id].available = True
        return "Yay"
    else:
        return "Nay "


@main.route('/mark_bin_unavailable/<bin_id>')
def mark_bin_unavailable(bin_id):
    if bin_id in bins.keys():
        bins[bin_id].available = False
        return "Yay"
    else:
        return "Nay "


@main.route('/mark_bin_online/<bin_id>')
def mark_bin_online(bin_id):
    if bin_id in bins.keys():
        bins[bin_id].online = True
        return "Yay"
    else:
        return "Nay "


@main.route('/mark_bin_offline/<bin_id>')
def mark_bin_offline(bin_id):
    if bin_id in bins.keys():
        bins[bin_id].online = False
        return "Yay"
    else:
        return "Nay "


@main.route('/check_bar_code/<barcode>')
def check_bar_code(barcode):
    if barcode in barcodes:
        return "Yay"
    else:
        return "Nay"
