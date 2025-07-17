from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import EmailType
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from sqlalchemy import or_, and_, select
from datetime import datetime

app  =  Flask(__name__)
app.secret_key  =  'your_security_key'

# Configure SQL Alchemy for User Database
app.config["SQLALCHEMY_DATABASE_URI"]  =  "sqlite:///data.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]  =  False
db  =  SQLAlchemy(app)


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
        self.password  =  password

    def check_password(self, password):
        return self.password  ==  password
    
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
    spot_id  =  db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable = False)
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
    
#Modified Admin Views

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return session.get('is_admin', False)

    def inaccessible_callback(self, name):
        return redirect(url_for('login'))

class SecureModelView(ModelView):
    def is_accessible(self):
        return session.get('is_admin', False)

    def inaccessible_callback(self, name):
        return redirect(url_for('login'))

class UserAdmin(SecureModelView):
    column_list  =  ['id', 'email', 'name', 'is_admin']
    form_columns  =  ['email', 'password', 'name', 'phone', 'address', 'pincode', 'is_admin']
    can_create  =  True
    can_edit  =  False
    can_delete  =  True
    column_sortable_list  =  ['id', 'name', 'is_admin']
    column_searchable_list  =  ['id', 'email', 'name', 'phone', 'address', 'pincode']
    column_default_sort  =  'id'

class ParkingLotAdmin(SecureModelView):
    column_list  =  ['id', 'prime_location_name', 'max_spots', 'price_per_hour', 'address', 'pincode', 'is_active']
    column_searchable_list = ['prime_location_name', 'address', 'pincode']
    column_sortable_list = ['id', 'prime_location_name', 'address', 'price_per_hour', 'is_active']
    def on_model_change(self, form, model, is_created):
        db.session.flush()

        if is_created:
            for i in range(1, model.max_spots + 1):
                spot = ParkingSpot(id = f"L{model.id}_S{i}", lot_id = model.id)
                db.session.add(spot)

        else:
            old_spots = ParkingSpot.query.filter_by(lot_id = model.id).all()
            old_spots_count = len(old_spots)
            if old_spots_count != model.max_spots:
                all_unreserved = True
                for spot in old_spots:
                    if spot.is_reserved:
                        all_unreserved = False
                        break
                if not all_unreserved:
                    raise ValueError("Cannot change max spots: some spots are currently reserved.")
                
                if all_unreserved:
                    for spot in old_spots:
                        db.session.delete(spot)
                    db.session.flush()
                    for i in range(1, model.max_spots + 1):
                        new_spot = ParkingSpot(id = f"L{model.id}_S{i}", lot_id = model.id)
                        db.session.add(new_spot)





class ParkingSpotAdmin(SecureModelView):
    column_list  =  ['id', 'lot', 'is_reserved']
    form_columns  =  ['lot']
    column_sortable_list = ['id', 'is_reserved']
    column_searchable_list = ['lot.prime_location_name', 'id']
    can_edit = False
    can_create = False
    can_delete = False
    def on_model_change(self,  model, is_created):
        db.session.flush()

        if is_created:
            lot = ParkingLot.query.filter_by(id = model.lot_id).first()
            lot.max_spots += 1
            db.session.commit()
        
    

    # Use form_ajax_refs for the relationship field
    form_ajax_refs  =  {
        'lot': {
            'fields': ['prime_location_name', 'address', 'pincode', 'id'],
            'page_size': 10
        }
    }

class ReservationAdmin(SecureModelView):

    column_list  =  ['id', 'spot', 'user', 'parking_timestamp']
    # form_columns  =  ['spot', 'user', 'parking_timestamp']
    can_create  =  False
    can_edit  =  False
    can_delete  =  True
    # form_ajax_refs  =  {
    #     'spot': {
    #         'fields': ['spot_number', 'lot_id'],
    #         'page_size': 10
    #     },
    #     'user': {
    #         'fields': ['email', 'name'],
    #         'page_size': 10
    #     }
    # }
class PastReservationsAdmin(SecureModelView):
    column_list = ['id', 'user_email', 'lot_prime_location', 'address', 'pincode', 'parking_timestamp', 'leaving_timestamp', 'vehicle_number']
    column_sortable_list = ['id', 'user_email', 'lot_prime_location', 'address', 'parking_timestamp', 'leaving_timestamp', 'total_cost']
    column_searchable_list = ['user_email', 'lot_prime_location', 'address', 'pincode']
    can_create  =  False
    can_edit  =  False
    can_delete  =  False



# admin functionality
app.config['FLASK_ADMIN_SWATCH']  =  'cosmo'
admin  =  Admin(app, name = 'Admin Panel', template_mode = 'bootstrap3', index_view = MyAdminIndexView())

admin.add_view(UserAdmin(User, db.session))
admin.add_view(ParkingLotAdmin(ParkingLot, db.session))
admin.add_view(ParkingSpotAdmin(ParkingSpot, db.session))
admin.add_view(ReservationAdmin(Reservation, db.session, name = "Current Reservations"))
admin.add_view(PastReservationsAdmin(PastReservations, db.session))


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



# Routes

@app.route('/')
def home():
    if "email" in session:
        if session.get('is_admin'):
            return redirect('/admin')
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method  ==  'POST':
        email  =  request.form['email']
        password  =  request.form['password']
        user  =  User.query.filter_by(email = email).first()
        
        if user and user.check_password(password):
            session['email']  =  email
            session['is_admin']  =  user.is_admin
            next_page  =  request.args.get('next')
            return redirect(next_page or (url_for('dashboard') if not user.is_admin else url_for('admin.index')))
        else:
            return render_template('security/ulogin.html', error = "Invalid credentials")

    return render_template('security/ulogin.html')



@app.route('/register', methods  =  ['GET', 'POST'])  
def register():
    if request.method  ==  'POST':
        email  =  request.form['email']
        password  =  request.form['password']
        user  =  User.query.filter_by(email  =  email).first()
        name  =  request.form['name']
        phone  =  request.form['phone']
        address  =  request.form['address']
        pincode  =  request.form['pincode']

        if user:
            return render_template("security/uregist.html", error  =  "User already exists")
        else:
            new_user  =  User(email = email, name = name, phone = phone, address = address, pincode = pincode, is_admin  =  False)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            session['email']  =  email
            return redirect(url_for('dashboard'))
    return render_template('security/uregist.html')

@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('is_admin', None)
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    user  =  User.query.filter_by(email = session['email']).first()
    cur_reservations  =  Reservation.query.join(User).filter(User.email  ==  session['email']).all()
    past_reservations = PastReservations.query.filter_by(user_email = session['email']).order_by(PastReservations.leaving_timestamp.desc()).all()
    return render_template('dashboard.html', user = user, cur_reservations  =  cur_reservations, past_reservations = past_reservations)

@app.route('/profile', methods  =  ['GET', 'POST'])
def profile():
    if 'email' not in session:
        return redirect(url_for('login'))
    user  =  User.query.filter_by(email  =  session['email']).first()
    if user.is_admin is True:
        return render_template('admin/profile.html', user  =  user)
    return render_template('profile.html', user  =  user)

@app.route('/updateprofile', methods  =  ['GET','POST'])
def updateprofile():
    if 'email' not in session:
        return redirect(url_for('login'))
    if request.method  ==  'POST':
        user  =  User.query.filter_by(email  =  session['email']).first()
        if user.is_admin is True:
            password  =  request.form['password']
            name  =  request.form['name']
            user.password  =  password
            user.name  =  name
            db.session.commit()
            return redirect(url_for('admin.index'))

        password  =  request.form['password']
        phone  =   request.form['phone']
        name  =  request.form['name']
        address  =  request.form['address']
        pincode  =  request.form['pincode']

        user.password  =  password
        user.phone  =  phone
        user.name  =  name
        user.address  =  address
        user.pincode  =  pincode

        db.session.commit()
        return redirect(url_for('dashboard'))


@app.route('/search', methods  =  ['GET','POST'])
def search():
    if request.method  ==  'GET':
        user  =  User.query.filter_by(email = session['email']).first()
        q  =  request.args.get('query')
        if q:
            results = (
                db.session.query(ParkingLot)
                .join(ParkingSpot)
                .filter(
                    and_(
                        or_(
                            ParkingLot.prime_location_name.ilike(f"%{q}%"),
                            ParkingLot.pincode.ilike(f"%{q}%"),
                            ParkingLot.address.ilike(f"%{q}%")
                        ),
                        ParkingSpot.is_reserved == False
                    )
                )
                .distinct()
                .all()

            )

            cur_reservations  =  Reservation.query.join(User).filter(User.email  ==  session['email']).all()
            past_reservations = PastReservations.query.filter_by(user_email = session['email']).order_by(PastReservations.leaving_timestamp.desc()).all()
            return render_template('dashboard.html', user = user, results = results, cur_reservations = cur_reservations, past_reservations = past_reservations)
        
@app.route('/booking-confirmation', methods  =  ['POST', 'GET'])
def booking_confirmation():
    if request.method  ==  'POST':
        lot_id  =  request.form.get('lot_id')
        spot  =  ParkingSpot.query.filter_by(lot_id = lot_id, is_reserved = False).first()
        user  =  User.query.filter_by(email = session['email']).first()
        if spot and user:
            return render_template('booking.html', spot = spot)

@app.route('/bookspot', methods = ['POST'])
def bookspot():
    if 'email' not in session:
        return redirect(url_for('login'))

    spot_id  =  request.form.get('spot_id')
    vehicle_number = request.form.get('vehicle_number')
    user  =  User.query.filter_by(email = session['email']).first()
    spot  =  ParkingSpot.query.filter_by(id = spot_id).first()
    parking_timestamp  =  datetime.now()

    if spot and user:
        reservation  =  Reservation(
            spot_id = spot.id,
            user_id = user.id,
            parking_timestamp = parking_timestamp,
            vehicle_number = vehicle_number
        )
        spot.is_reserved  =  True
        db.session.add(reservation)
        db.session.commit()
        return redirect(url_for('dashboard'))
        
@app.route('/release', methods  =  ['POST'])
def release():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    reservation_id  =  request.form.get('reservation_id')
    reservation  =  Reservation.query.filter(Reservation.id  ==  reservation_id).first()
    spot  =  ParkingSpot.query.filter(ParkingSpot.id  ==  reservation.spot_id).first()
    user  =  User.query.filter_by(email = session['email']).first()
    parking_timestamp  =  reservation.parking_timestamp
    leaving_timestamp  =  datetime.now()
    hours_parked  =  (leaving_timestamp - parking_timestamp).total_seconds() / 3600

    if user and reservation:
        spot.is_reserved  =  False
        record = PastReservations(user_email = user.email, 
                                  lot_prime_location = spot.lot.prime_location_name, 
                                  address = spot.lot.address, 
                                  pincode = spot.lot.pincode, 
                                  parking_timestamp = parking_timestamp,
                                  leaving_timestamp = leaving_timestamp,
                                  vehicle_number = reservation.vehicle_number,
                                  total_cost = spot.lot.price_per_hour * hours_parked)
        db.session.add(record)
        db.session.delete(reservation)
        db.session.commit()
        return redirect(url_for('dashboard'))
        


if __name__  ==  '__main__':
    with app.app_context():
        db.create_all() 
        create_admin_user()
    app.run(debug = True)