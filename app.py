from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import EmailType
from flask_admin import Admin, AdminIndexView

from flask_admin.contrib.sqla import ModelView
from sqlalchemy import or_

app = Flask(__name__)
app.secret_key = 'your_security_key'

# Configure SQL Alchemy for User Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# Database Models
class User(db.Model):
    # Class Variables
    id  = db.Column(db.Integer, primary_key = True, autoincrement = True)
    email = db.Column(EmailType, unique=True, nullable=False)
    password = db.Column(db.String(150), nullable = False)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(10))
    address = db.Column(db.String(255))
    pincode = db.Column(db.String(10))
    is_admin = db.Column(db.Boolean, default=False)
    reservations = db.relationship('Reservation', back_populates = 'user')
    def set_password(self, password):
        self.password = password

    def check_password(self, password):
        return self.password == password
    
    def __repr__(self):
        return f"{self.email} (id: {self.id})"

class ParkingLot(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    prime_location_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    contact_number = db.Column(db.String(15))
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    spots = db.relationship('ParkingSpot', back_populates='lot')
    def __repr__(self):
        return f"{self.prime_location_name} (Lot id: {self.id})"

class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    spot_number = db.Column(db.String(10), nullable=False) # like 'A1'
    price_per_hour = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(1), default='A')  # 'A' for available, 'O' for occupied
    vehicle_type = db.Column(db.String(20), default='4-wheeler')  # Can be '2-wheeler' etc.
    is_reserved = db.Column(db.Boolean, default=False)
    lot = db.relationship('ParkingLot', back_populates='spots')
    reservations = db.relationship('Reservation', back_populates = 'spot')
    def __repr__(self):
        return f"Lot: {self.lot_id} (Spot id: {self.id})"

    
class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parking_timestamp = db.Column(db.DateTime, nullable=False)
    leaving_timestamp = db.Column(db.DateTime)
    total_cost = db.Column(db.Float)
    spot = db.relationship('ParkingSpot', back_populates = 'reservations')
    user = db.relationship('User', back_populates = 'reservations')
    def __repr__(self):
        return f"User: {self.user.email} Spot: {self.spot_id} (Res. id: {self.id})"
    
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

class UserAdmin(ModelView):
    column_list = ['id', 'email', 'name', 'is_admin']

class ParkingLotAdmin(ModelView):
    column_list = ['id', 'prime_location_name', 'address', 'pincode', 'contact_number', 'is_active']
    
class ParkingSpotAdmin(ModelView):
    column_list = ['id', 'lot', 'spot_number','price_per_hour', 'status', 'vehicle_type', 'is_reserved']
    form_columns = ['lot', 'spot_number', 'price_per_hour', 'status', 'vehicle_type', 'is_reserved']
    
    # Use form_ajax_refs for the relationship field
    form_ajax_refs = {
        'lot': {
            'fields': ['prime_location_name', 'address', 'pincode', 'id'],
            'page_size': 10
        }
    }

class ReservationAdmin(ModelView):
    column_list = ['id', 'spot', 'user', 'parking_timestamp', 'leaving_timestamp', 'total_cost']
    form_columns = ['spot', 'user', 'parking_timestamp', 'leaving_timestamp', 'total_cost']

    # Corrected form_ajax_refs
    form_ajax_refs = {
        'spot': {
            'fields': ['spot_number', 'lot_id'],
            'page_size': 10
        },
        'user': {
            'fields': ['email', 'name'],
            'page_size': 10
        }
    }



# admin functionality
app.config['FLASK_ADMIN_SWATCH'] = 'cosmo'
admin = Admin(app, name='Admin Panel', template_mode='bootstrap3', index_view=MyAdminIndexView())

admin.add_view(SecureModelView(User, db.session))
admin.add_view(SecureModelView(ParkingLot, db.session))
admin.add_view(SecureModelView(ParkingSpot, db.session))
admin.add_view(SecureModelView(Reservation, db.session))

# Create admin user if not exists
def create_admin_user():
    admin_email = 'admin@gmail.com'
    admin_password = 'admin123'
    admin_user = User.query.filter_by(email=admin_email).first()
    if not admin_user:
        admin_user = User(email=admin_email, is_admin=True)
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['email'] = email
            session['is_admin'] = user.is_admin
            next_page = request.args.get('next')
            return redirect(next_page or (url_for('dashboard') if not user.is_admin else url_for('admin.index')))
        else:
            return render_template('security/ulogin.html', error="Invalid credentials")

    return render_template('security/ulogin.html')



@app.route('/register', methods = ['GET', 'POST'])  
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email = email).first()
        phone = request.form.get('phone')
        address = request.form.get('address')
        pincode = request.form.get('pincode')

        if user:
            return render_template("security/uregist.html", error = "User already exists")
        else:
            new_user = User(email = email, phone=phone, address=address, pincode=pincode, is_admin = False)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            session['email'] = email
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
    
    user = User.query.filter_by(email=session['email']).first()
    return render_template('dashboard.html', user=user)

@app.route('/search', methods = ['GET','POST'])
def search():
    if request.method == 'GET':
        user = User.query.filter_by(email=session['email']).first()
        q = request.args.get('query')
        results = []
        if q:
            results = ParkingSpot.query.join(ParkingLot).filter(or_(
                    ParkingLot.prime_location_name.ilike(f"%{q}%"),
                    ParkingLot.pincode.ilike(f"%{q}%"),
                    ParkingLot.address.ilike(f"%{q}%")
                )).limit(10).all()

        return render_template("dashboard.html", user = user, results = results)


if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
        create_admin_user()
    app.run(debug=True)