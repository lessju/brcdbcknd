import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()


def load_barcodes_data(app):
    # Load barcode database
    from backend.models import RecyclableContainer

    with app.app_context():
        with open("backend/database/barcodes.txt") as f:
            for line in f.readlines():
                barcode, label, weight, value = line.split(',')
                if not RecyclableContainer.query.filter_by(barcode=barcode).first():
                    new_container = RecyclableContainer(barcode=int(barcode),
                                                        label=label, weight=weight,
                                                        monetary_value=float(value))
                    db.session.add(new_container)

        db.session.commit()


def load_users(app):
    # Load users
    from backend.models import User

    with app.app_context():
        with open("backend/database/users.txt") as f:
            for line in f.readlines():
                name, email, password, id = line.split(',')
                if not User.query.filter_by(email=email).first():
                    new_user = User(id=id,
                                    email=email,
                                    name=name,
                                    password=password)
                    db.session.add(new_user)
        db.session.commit()


def create_app(*args, **kwargs):
    """ Create Flask application """

    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'TESTING'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from backend.models import User

    @login_manager.user_loader
    def load_user(user_id):
        # Since the user_id is the primary key, use it in the query for the user
        return User.query.get(int(user_id))

    # Create database
    with app.app_context():
        db.create_all()

    # blueprint for auth routes in our app
    from backend.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    from backend.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Load static data
    load_barcodes_data(app)
    load_users(app)

    return app


# Create application instance
application = create_app()


def update_bin_state():
    """ Function called by scheduler that check the last modified time of recycling bins """

    with application.app_context():
        from backend.models import RecyclingBin

        # Cycle through all the registered recycling bins
        for recycling_bin in RecyclingBin.query.all():
            # If bin is already marked as offline, continue
            if not recycling_bin.online:
                continue

            # If the last modified date of the bin
            if (datetime.datetime.utcnow() - recycling_bin.modified_time).seconds > 300:
                recycling_bin.available = False
                recycling_bin.online = False
                db.session.commit()
    return


# Every minute update the status of recycling bins
sched = BackgroundScheduler(daemon=True)
sched.add_job(update_bin_state, 'interval', minutes=1)
sched.start()


if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5000, use_reloader=False)
