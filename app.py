from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy


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
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    



















# Routes

@app.route('/')
def home():
    if "email" in session:
        return redirect(url_for('udashboard'))
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
            return redirect(url_for('dashboard'))
        else:
            return render_template('security/ulogin.html', error = "Invalid User Credentials")
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

@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect(url_for('login'))
    return render_template('udashboard.html')



if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all() 
    app.run(debug=True)