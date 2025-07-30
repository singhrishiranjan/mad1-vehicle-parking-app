from flask import Flask
from flask_admin import Admin
from admin.views import *
from config import Config
from routes import register_routes
from models.models import *



def create_app():
    app  =  Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app) 
    register_routes(app)

    # admin functionality
    admin  =  Admin(app, name = 'Admin Panel', template_mode = 'bootstrap3', index_view = MyAdminIndexView())

    admin.add_view(UserAdmin(User, db.session))
    admin.add_view(ParkingLotAdmin(ParkingLot, db.session))
    admin.add_view(ParkingSpotAdmin(ParkingSpot, db.session))
    admin.add_view(ReservationAdmin(Reservation, db.session, name = "Current Reservations"))
    admin.add_view(PastReservationsAdmin(PastReservations, db.session))

    return app


# Create admin user if not exists
def create_admin_user():
    admin_email  =  'admin@gmail.com'
    admin_password  =  'admin123'
    admin_user  =  User.query.filter_by(is_admin  =  True).first()
    if not admin_user:
        admin_user  =  User(email = admin_email, is_admin = True)
        admin_user.set_password(admin_password)
        db.session.add(admin_user)
        db.session.commit()



app = create_app()


if __name__  ==  '__main__':
    with app.app_context():
        db.create_all() 
        create_admin_user()
    app.run(debug = True)