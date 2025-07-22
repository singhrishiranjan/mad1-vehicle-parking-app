from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy_utils import EmailType


db = SQLAlchemy()






# Database Models
class User(db.Model):
    # Class Variables
    id   =  db.Column(db.Integer, primary_key  =  True, autoincrement  =  True)
    email  =  db.Column(EmailType, nullable = False)
    password  =  db.Column(db.String(150), nullable  =  False)
    name  =  db.Column(db.String(100))
    phone  =  db.Column(db.String(10))
    address  =  db.Column(db.String(255))
    pincode  =  db.Column(db.String(10))
    is_admin  =  db.Column(db.Boolean, default = False)
    reservations  =  db.relationship('Reservation', back_populates  =  'user')
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def __repr__(self):
        return f"{self.email} (id: {self.id})"

class ParkingLot(db.Model):
    id  =  db.Column(db.Integer, primary_key = True, autoincrement  =  True)
    prime_location_name  =  db.Column(db.String(100), nullable = False)
    address  =  db.Column(db.String(255), nullable = False)
    pincode  =  db.Column(db.String(10), nullable = False)
    contact_number  =  db.Column(db.String(15))
    max_spots  =  db.Column(db.Integer, default  =  1)
    price_per_hour  =  db.Column(db.Integer, nullable = False, default = 0)
    is_active  =  db.Column(db.Boolean, default = True)
    spots  =  db.relationship('ParkingSpot', back_populates = 'lot')
    def __repr__(self):
        return f"{self.prime_location_name} (Lot id: {self.id})"

class ParkingSpot(db.Model):
    id  =  db.Column(db.String(10), primary_key = True)
    lot_id  =  db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable = False)
    is_reserved  =  db.Column(db.Boolean, default = False)
    lot  =  db.relationship('ParkingLot', back_populates = 'spots')
    reservations  =  db.relationship('Reservation', back_populates  =  'spot')
    def __repr__(self):
        return f"Spot id: {self.id}"

    
class Reservation(db.Model):
    id  =  db.Column(db.Integer, primary_key = True, autoincrement  =  True)
    spot_id  =  db.Column(db.String(10), db.ForeignKey('parking_spot.id'), nullable = False)
    user_id  =  db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    parking_timestamp  =  db.Column(db.DateTime, nullable = False)
    vehicle_number  =  db.Column(db.String(20))
    spot  =  db.relationship('ParkingSpot', back_populates  =  'reservations')
    user  =  db.relationship('User', back_populates  =  'reservations')
    def __repr__(self):
        return f"User: {self.user.email} Spot: {self.spot_id} (Res. id: {self.id})"
    
class PastReservations(db.Model):
    id  =  db.Column(db.Integer, primary_key = True, autoincrement  =  True)
    user_email  =  db.Column(EmailType)
    lot_prime_location  =  db.Column(db.String(100))
    address  =  db.Column(db.String(255), nullable = False)
    pincode  =  db.Column(db.String(10), nullable = False)
    parking_timestamp  =  db.Column(db.DateTime)
    leaving_timestamp  =  db.Column(db.DateTime)
    vehicle_number  =  db.Column(db.String(20))
    total_cost  =  db.Column(db.Float)
    def __repr__(self):
        return f"User: {self.user_email} (id: {self.id})"
    