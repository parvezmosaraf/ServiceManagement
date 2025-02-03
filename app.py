from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'client', 'agent', 'admin'

class ServiceBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_details = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default='Pending')

class Receipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receipt_url = db.Column(db.String(255), nullable=False)

class TaskAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_details = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default='Assigned')

def is_valid_password(password):
    return bool(re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$', password))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        if not is_valid_password(password):
            flash("Password must contain at least one uppercase, one lowercase letter, and one number.", "danger")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials", "danger")
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', role=session.get('role'))

@app.route('/book_service', methods=['POST'])
def book_service():
    if 'user_id' not in session or session['role'] != 'client':
        return redirect(url_for('login'))
    
    service_details = request.form['service_details']
    booking = ServiceBooking(client_id=session['user_id'], service_details=service_details)
    db.session.add(booking)
    db.session.commit()
    flash("Service booked successfully!", "success")
    return redirect(url_for('dashboard'))

@app.route('/upload_receipt', methods=['POST'])
def upload_receipt():
    if 'user_id' not in session or session['role'] != 'client':
        return redirect(url_for('login'))
    
    receipt_url = request.form['receipt_url']
    receipt = Receipt(client_id=session['user_id'], receipt_url=receipt_url)
    db.session.add(receipt)
    db.session.commit()
    flash("Receipt uploaded successfully!", "success")
    return redirect(url_for('dashboard'))

@app.route('/assign_task', methods=['POST'])
def assign_task():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    agent_id = request.form['agent_id']
    task_details = request.form['task_details']
    task = TaskAssignment(agent_id=agent_id, task_details=task_details)
    db.session.add(task)
    db.session.commit()
    flash("Task assigned successfully!", "success")
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    flash("Logged out successfully!", "info")
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
