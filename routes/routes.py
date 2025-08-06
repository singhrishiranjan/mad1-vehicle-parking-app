# Routes
from flask import session, redirect, url_for, request, render_template, Blueprint
from models.models import db, User, ParkingLot, ParkingSpot, Reservation, PastReservations
from datetime import datetime, timedelta
from sqlalchemy import or_, and_, func


routes_bp = Blueprint('routes_bp', __name__)


@routes_bp.route('/')
def home():
    if "email" in session:
        if session.get('is_admin'):
            return redirect(url_for('admin.index'))
        return redirect(url_for('routes_bp.dashboard'))
    return render_template('index.html')

@routes_bp.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method  ==  'POST':
        email  =  request.form['email']
        password  =  request.form['password']
        user  =  User.query.filter_by(email = email).first()
        
        if user and user.check_password(password):
            session['email']  =  email
            session['is_admin']  =  user.is_admin
            next_page  =  request.args.get('next')
            return redirect(next_page or (url_for('routes_bp.dashboard') if not user.is_admin else url_for('admin.index')))
        else:
            return render_template('security/ulogin.html', error = "Invalid credentials")

    return render_template('security/ulogin.html')



@routes_bp.route('/register', methods  =  ['GET', 'POST'])  
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
            return redirect(url_for('routes_bp.dashboard'))
    return render_template('security/uregist.html')

@routes_bp.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('is_admin', None)
    return redirect(url_for('routes_bp.home'))

@routes_bp.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect(url_for('routes_bp.login'))
    
    user  =  User.query.filter_by(email = session['email']).first()
    cur_reservations  =  Reservation.query.join(User).filter(User.email  ==  session['email']).all()

    past_reservations = PastReservations.query.filter_by(user_email = session['email']).order_by(PastReservations.leaving_timestamp.desc()).all()
    return render_template('dashboard.html', user = user, cur_reservations  =  cur_reservations, past_reservations = past_reservations)

@routes_bp.route('/profile', methods  =  ['GET', 'POST'])
def profile():
    if 'email' not in session:
        return redirect(url_for('routes_bp.login'))
    user  =  User.query.filter_by(email  =  session['email']).first()
    if user.is_admin is True:
        return render_template('admin/profile.html', user  =  user)
    return render_template('profile.html', user  =  user)

@routes_bp.route('/updateprofile', methods  =  ['GET','POST'])
def updateprofile():
    if 'email' not in session:
        return redirect(url_for('routes_bp.login'))
    if request.method  ==  'POST':
        user  =  User.query.filter_by(email  =  session['email']).first()
        if user.is_admin is True:
            name  =  request.form['name']
            user.name  =  name
            db.session.commit()
            return redirect(url_for('admin.index'))
        phone  =   request.form['phone']
        name  =  request.form['name']
        address  =  request.form['address']
        pincode  =  request.form['pincode']

        user.phone  =  phone
        user.name  =  name
        user.address  =  address
        user.pincode  =  pincode

        db.session.commit()
        return redirect(url_for('routes_bp.dashboard'))


@routes_bp.route('/search', methods  =  ['GET','POST'])
def search():
    if request.method  ==  'GET':
        user  =  User.query.filter_by(email = session['email']).first()
        q  =  request.args.get('query')
        results =[]
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
        
@routes_bp.route('/booking-confirmation', methods  =  ['POST', 'GET'])
def booking_confirmation():
    if request.method  ==  'POST':
        lot_id  =  request.form.get('lot_id')
        spot  =  ParkingSpot.query.filter_by(lot_id = lot_id, is_reserved = False).first()
        user  =  User.query.filter_by(email = session['email']).first()
        if spot and user:
            return render_template('booking.html', spot = spot, user=user)

@routes_bp.route('/bookspot', methods = ['POST'])
def bookspot():
    if 'email' not in session:
        return redirect(url_for('routes_bp.login'))

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
        return redirect(url_for('routes_bp.dashboard'))

@routes_bp.route('/releasing-confirmation', methods = ['POST'])
def releasing_confirmation():
    if request.method == 'POST':
        res_id = request.form.get('reservation_id')
        res = Reservation.query.filter_by(id = res_id).first()
        parking_timestamp  =  res.parking_timestamp
        user  =  User.query.filter_by(email = session['email']).first()

        cur_time = datetime.now()
        es_cost = ((cur_time - parking_timestamp).total_seconds() / 3600) * res.spot.lot.price_per_hour
        if res and user:
            return render_template('releasespot.html', user = user, res = res, cur_time = cur_time, es_cost = es_cost)
        
@routes_bp.route('/release', methods  =  ['POST'])
def releasespot():
    if 'email' not in session:
        return redirect(url_for('routes_bp.login'))
    
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
        return redirect(url_for('routes_bp.dashboard'))
        
@routes_bp.route('/summary', methods = ['GET'])
def summary():
    user  =  User.query.filter_by(email = session['email']).first()
   

    end_date = datetime.now()
    start_date = end_date - timedelta(days = 6)
    dates = [start_date + timedelta(days = x) for x in range(7)]


    records = PastReservations.query.filter(
        PastReservations.user_email == user.email,
        PastReservations.parking_timestamp.between(start_date, end_date + timedelta(days=1))
    ).all()

    results = PastReservations.query.filter(
        PastReservations.user_email == user.email,
        PastReservations.leaving_timestamp.between(start_date, end_date + timedelta(days = 1))
    ).all()

    res_counts = {date.strftime('%d-%m-%Y'): 0 for date in dates}
    for record in records:
        res_counts[record.parking_timestamp.strftime('%d-%m-%Y')] += 1
    res_counts_sorted = dict(sorted(res_counts.items()))

    cost_counts = {date.strftime('%d-%m-%Y') : 0 for date in dates}
    for result in results:
        cost_counts[result.leaving_timestamp.strftime('%d-%m-%Y')] += result.total_cost
    cost_counts_sorted = dict(sorted(cost_counts.items()))

    labels =[date for date in res_counts_sorted.keys()]
    res_values = [count for count in res_counts_sorted.values()]
    cost_values = [cost for cost in cost_counts_sorted.values()]


    return render_template('summary.html', user = user, labels = labels, res_values = res_values, cost_values = cost_values)

@routes_bp.route('/admin/summary', methods = ['GET', 'POST'])
def admin_summary():
    user  =  User.query.filter_by(email = session['email']).first()
    if user.is_admin == True:
        total_spots = ParkingSpot.query.count()
        reserved_spots = ParkingSpot.query.filter(ParkingSpot.is_reserved == True).count()
        unreserved_spots = total_spots - reserved_spots

    end_date = datetime.now()
    start_date = end_date - timedelta(days = 6)
    dates = [start_date + timedelta(days = x) for x in range(7)]

    records = PastReservations.query.filter(
        PastReservations.leaving_timestamp.between(start_date, end_date + timedelta(days=1))
    ).all()

    rev_counts = {date.strftime('%d-%m-%Y') : 0 for date in dates}
    for record in records:
        rev_counts[record.leaving_timestamp.strftime('%d-%m-%Y')] += record.total_cost

    rev_counts_sorted = dict(sorted(rev_counts.items()))
    labels =[date for date in rev_counts_sorted.keys()]
    rev_values = [rev for rev in rev_counts_sorted.values()]

    return render_template('admin/summary.html', reserved_spots = reserved_spots, unreserved_spots = unreserved_spots, labels = labels, rev_values = rev_values)
