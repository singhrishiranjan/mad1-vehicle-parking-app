from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView


app = Flask(__name__)
app.secret_key = 'your_security_key'

# Configure SQL Alchemy
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
# Database Model
class User(db.Model):
    # Class Variables
    id  = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(50), unique = True, nullable = False)
    password = db.Column(db.String(150), nullable = False)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(10))
    address = db.Column(db.String(255))
    pincode = db.Column(db.String(10))
    is_admin = db.Column(db.Boolean, default=False)
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    

# admin functionality
admin = Admin(app, name='Admin Panel', template_mode='bootstrap3')
admin.add_view(ModelView(User, db.session))


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

@app.route('/login', methods = ['GET','POST'])
def login():
    #Collect stuff from form
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email = email).first()
        
        if user and user.check_password(password):
            session['email'] = email
            if user.is_admin:
                session['is_admin'] = True
                return redirect('/admin')
            return redirect(url_for('dashboard'))
        return render_template('security/ulogin.html', error="Invalid User Credentials")
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
            new_user = User(email = email, phone=phone, address=address, pincode=pincode,)
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


if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
        create_admin_user()
    app.run(debug=True)