from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder='.')
app.secret_key = "supersecretkey"

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school.db'
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin', 'teacher', 'student'

# Timetable model
class Timetable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(20), nullable=False)
    period = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    teacher = db.Column(db.String(100), nullable=True)
    classroom = db.Column(db.String(50), nullable=True)

# Notes model
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

# Doubt model
class Doubt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='open')  # open, answered, closed
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

# Meeting model
class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    participants = db.Column(db.Text, nullable=True)  # comma separated user ids or JSON string
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

# Chat message model
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

# Inquiry model
class Inquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='open')  # open, in_progress, resolved
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

# SubstitutionTeacher model
class SubstitutionTeacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    substitute_teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

# UserSettings model
class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_enabled = db.Column(db.Boolean, default=True)
    notifications_enabled = db.Column(db.Boolean, default=True)
    dashboard_layout = db.Column(db.String(100), default='default')
    pdf_viewer_enabled = db.Column(db.Boolean, default=True)
    bookmarks = db.Column(db.Text, nullable=True)  # JSON string of bookmarks

# Routes
@app.route('/')
def home():
    timetable = Timetable.query.all()
    return render_template('index.html', timetable=timetable)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash("Invalid credentials")
    return render_template('signin.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        if not username or not password or not role:
            flash("All fields are required")
            return redirect(url_for('signup'))

        if len(password) < 6:
            flash("Password must be at least 6 characters long")
            return redirect(url_for('signup'))

        if role not in ['admin', 'teacher', 'student']:
            flash("Invalid role")
            return redirect(url_for('signup'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists")
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash("Account created successfully! Please log in.")
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    timetable = Timetable.query.all()
    return render_template('admin panel.html', timetable=timetable)

@app.route('/admin/add', methods=['POST'])
def add_timetable():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    day = request.form['day']
    period = request.form['period']
    subject = request.form['subject']
    teacher = request.form['teacher']
    classroom = request.form['classroom']
    new_entry = Timetable(day=day, period=period, subject=subject, teacher=teacher, classroom=classroom)
    db.session.add(new_entry)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/teacher')
def teacher_dashboard():
    if session.get('role') != 'teacher':
        return redirect(url_for('home'))
    return render_template('manageteachers.html')

@app.route('/student')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('home'))
    return render_template('student.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# API route to handle classroom booking submission
@app.route('/book_classroom', methods=['POST'])
def book_classroom():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400

    # Extract booking details
    user_id = session['user_id']
    event_title = data.get('eventTitle')
    event_date = data.get('eventDate')
    time_slot = data.get('timeSlot')
    duration = data.get('duration')
    classroom_name = data.get('classroom', {}).get('name')
    teacher_name = data.get('classroom', {}).get('type')  # Assuming teacher info not provided here
    description = data.get('description')
    equipment = data.get('equipment', [])

    if not all([event_title, event_date, time_slot, duration, classroom_name]):
        return jsonify({'error': 'Missing required booking information'}), 400

    # Create timetable entries for the duration (assuming 30 min slots)
    # For simplicity, create one entry per booking
    new_entry = Timetable(
        day=event_date,
        period=time_slot,
        subject=event_title,
        teacher=teacher_name,
        classroom=classroom_name
    )
    db.session.add(new_entry)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Classroom booked successfully'})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        session['user_id'] = user.id
        session['role'] = user.role
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'name': username,  # Using username as name for now
                'email': username,
                'role': user.role
            }
        })
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/auth/status')
def api_auth_status():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({
                'authenticated': True,
                'user': {
                    'id': user.id,
                    'name': user.username,
                    'email': user.username,
                    'role': user.role
                }
            })
    return jsonify({'authenticated': False}), 401


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
