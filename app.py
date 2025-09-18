
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder='.')
app.secret_key = "supersecretkey"

# Route for booking page

# Dynamic booking page: shows unavailable slots for selected classroom/date
@app.route('/book')
def book():
    from datetime import datetime
    classroom = request.args.get('classroom', None)
    event_date = request.args.get('date', None)
    unavailable_slots = []
    if classroom and event_date:
        # Convert date to weekday name
        try:
            weekday = datetime.strptime(event_date, "%Y-%m-%d").strftime("%A")
        except Exception:
            weekday = event_date
        # Query timetable for booked slots
        entries = Timetable.query.filter_by(classroom=classroom, day=weekday).all()
        unavailable_slots = [e.period for e in entries]
    return render_template('class booking.html', unavailable_slots=unavailable_slots)

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

# Meetings routes
@app.route('/meetings')
def meetings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    meetings = Meeting.query.filter((Meeting.organizer_id==user_id) | (Meeting.participants.like(f'%{user_id}%'))).order_by(Meeting.start_time.desc()).all()
    return render_template('meetings.html', meetings=meetings)

@app.route('/meetings/add', methods=['POST'])
def add_meeting():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    title = request.form.get('title')
    description = request.form.get('description')
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')
    location = request.form.get('location')
    participants = request.form.get('participants', '')
    if not all([title, start_time, end_time]):
        flash('Title, start time, and end time required.')
        return redirect(url_for('meetings'))
    meeting = Meeting(
        title=title,
        description=description,
        organizer_id=session['user_id'],
        participants=participants,
        start_time=start_time,
        end_time=end_time,
        location=location
    )
    db.session.add(meeting)
    db.session.commit()
    flash('Meeting scheduled!')
    return redirect(url_for('meetings'))

@app.route('/meetings/delete/<int:meeting_id>', methods=['POST'])
def delete_meeting(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    if meeting.organizer_id != session['user_id']:
        flash('Unauthorized.')
        return redirect(url_for('meetings'))
    db.session.delete(meeting)
    db.session.commit()
    flash('Meeting deleted!')
    return redirect(url_for('meetings'))

# Chat message model
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

# Direct chat routes
@app.route('/chat/<int:receiver_id>')
def chat(receiver_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    sender_id = session['user_id']
    messages = ChatMessage.query.filter(
        ((ChatMessage.sender_id==sender_id) & (ChatMessage.receiver_id==receiver_id)) |
        ((ChatMessage.sender_id==receiver_id) & (ChatMessage.receiver_id==sender_id))
    ).order_by(ChatMessage.timestamp.asc()).all()
    receiver = User.query.get(receiver_id)
    return render_template('chat.html', messages=messages, receiver=receiver)

@app.route('/chat/send/<int:receiver_id>', methods=['POST'])
def send_message(receiver_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    sender_id = session['user_id']
    message = request.form.get('message')
    if not message:
        flash('Message required.')
        return redirect(url_for('chat', receiver_id=receiver_id))
    chat_msg = ChatMessage(sender_id=sender_id, receiver_id=receiver_id, message=message)
    db.session.add(chat_msg)
    db.session.commit()
    return redirect(url_for('chat', receiver_id=receiver_id))

# Inquiry model
class Inquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='open')  # open, in_progress, resolved
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

# Inquiry routes
@app.route('/inquiries')
def inquiries():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    role = session.get('role')
    if role == 'student':
        inquiries = Inquiry.query.filter_by(student_id=user_id).order_by(Inquiry.created_at.desc()).all()
    elif role == 'teacher':
        inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
    else:
        inquiries = []
    return render_template('inquiries.html', inquiries=inquiries)

@app.route('/inquiries/submit', methods=['POST'])
def submit_inquiry():
    if session.get('role') != 'student':
        return redirect(url_for('home'))
    subject = request.form.get('subject')
    message = request.form.get('message')
    if not subject or not message:
        flash('Subject and message required.')
        return redirect(url_for('inquiries'))
    inquiry = Inquiry(student_id=session['user_id'], subject=subject, message=message)
    db.session.add(inquiry)
    db.session.commit()
    flash('Inquiry submitted!')
    return redirect(url_for('inquiries'))

@app.route('/inquiries/update/<int:inquiry_id>', methods=['POST'])
def update_inquiry(inquiry_id):
    inquiry = Inquiry.query.get_or_404(inquiry_id)
    status = request.form.get('status')
    if status not in ['open', 'in_progress', 'resolved']:
        flash('Invalid status.')
        return redirect(url_for('inquiries'))
    inquiry.status = status
    db.session.commit()
    flash('Inquiry status updated!')
    return redirect(url_for('inquiries'))

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

# Substitution teacher routes (admin only)
@app.route('/admin/substitutions')
def admin_substitutions():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    subs = SubstitutionTeacher.query.order_by(SubstitutionTeacher.start_date.desc()).all()
    teachers = User.query.filter_by(role='teacher').all()
    return render_template('substitutions.html', substitutions=subs, teachers=teachers)

@app.route('/admin/substitutions/add', methods=['POST'])
def add_substitution():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    original_teacher_id = request.form.get('original_teacher_id')
    substitute_teacher_id = request.form.get('substitute_teacher_id')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    reason = request.form.get('reason')
    if not all([original_teacher_id, substitute_teacher_id, start_date, end_date]):
        flash('All fields required.')
        return redirect(url_for('admin_substitutions'))
    sub = SubstitutionTeacher(
        original_teacher_id=original_teacher_id,
        substitute_teacher_id=substitute_teacher_id,
        start_date=start_date,
        end_date=end_date,
        reason=reason
    )
    db.session.add(sub)
    db.session.commit()
    flash('Substitution added!')
    return redirect(url_for('admin_substitutions'))

@app.route('/admin/substitutions/delete/<int:sub_id>', methods=['POST'])
def delete_substitution(sub_id):
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    sub = SubstitutionTeacher.query.get_or_404(sub_id)
    db.session.delete(sub)
    db.session.commit()
    flash('Substitution deleted!')
    return redirect(url_for('admin_substitutions'))

# UserSettings model
class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_enabled = db.Column(db.Boolean, default=True)
    notifications_enabled = db.Column(db.Boolean, default=True)
    dashboard_layout = db.Column(db.String(100), default='default')
    pdf_viewer_enabled = db.Column(db.Boolean, default=True)
    bookmarks = db.Column(db.Text, nullable=True)  # JSON string of bookmarks

# User settings routes
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    settings = UserSettings.query.filter_by(user_id=user_id).first()
    if request.method == 'POST':
        activity_enabled = bool(request.form.get('activity_enabled'))
        notifications_enabled = bool(request.form.get('notifications_enabled'))
        dashboard_layout = request.form.get('dashboard_layout', 'default')
        pdf_viewer_enabled = bool(request.form.get('pdf_viewer_enabled'))
        bookmarks = request.form.get('bookmarks', '')
        if not settings:
            settings = UserSettings(
                user_id=user_id,
                activity_enabled=activity_enabled,
                notifications_enabled=notifications_enabled,
                dashboard_layout=dashboard_layout,
                pdf_viewer_enabled=pdf_viewer_enabled,
                bookmarks=bookmarks
            )
            db.session.add(settings)
        else:
            settings.activity_enabled = activity_enabled
            settings.notifications_enabled = notifications_enabled
            settings.dashboard_layout = dashboard_layout
            settings.pdf_viewer_enabled = pdf_viewer_enabled
            settings.bookmarks = bookmarks
        db.session.commit()
        flash('Settings updated!')
        return redirect(url_for('settings'))
    return render_template('settings.html', settings=settings)

# Routes
@app.route('/')
def home():
    timetable = Timetable.query.all()
    return render_template('index.html', timetable=timetable)

# Notes feature routes
@app.route('/notes')
def notes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    notes = Note.query.filter_by(user_id=user_id).order_by(Note.created_at.desc()).all()
    return render_template('notes.html', notes=notes)

@app.route('/notes/add', methods=['POST'])
def add_note():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    title = request.form.get('title')
    content = request.form.get('content')
    if not title or not content:
        flash('Title and content are required.')
        return redirect(url_for('notes'))
    new_note = Note(user_id=session['user_id'], title=title, content=content)
    db.session.add(new_note)
    db.session.commit()
    flash('Note added successfully!')
    return redirect(url_for('notes'))

@app.route('/notes/delete/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    note = Note.query.get_or_404(note_id)
    if note.user_id != session['user_id']:
        flash('Unauthorized action.')
        return redirect(url_for('notes'))
    db.session.delete(note)
    db.session.commit()
    flash('Note deleted successfully!')
    return redirect(url_for('notes'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['username']
        password = request.form['password']
        # Try to find user by username or email
        user = User.query.filter((User.username == username_or_email)).first()
        if not user:
            # Try again for email-style usernames
            user = User.query.filter((User.username == username_or_email)).first()
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
    teachers = User.query.filter_by(role='teacher').all()
    return render_template('manageteachers.html', teachers=teachers)

# Teacher management routes (admin only)
@app.route('/admin/teachers')
def admin_teachers():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    teachers = User.query.filter_by(role='teacher').all()
    return render_template('manageteachers.html', teachers=teachers)

@app.route('/admin/teachers/add', methods=['POST'])
def add_teacher():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        flash('Username and password required.')
        return redirect(url_for('admin_teachers'))
    if User.query.filter_by(username=username).first():
        flash('Username already exists.')
        return redirect(url_for('admin_teachers'))
    hashed_password = generate_password_hash(password)
    new_teacher = User(username=username, password=hashed_password, role='teacher')
    db.session.add(new_teacher)
    db.session.commit()
    flash('Teacher added successfully!')
    return redirect(url_for('admin_teachers'))

@app.route('/admin/teachers/delete/<int:teacher_id>', methods=['POST'])
def delete_teacher(teacher_id):
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    teacher = User.query.get_or_404(teacher_id)
    if teacher.role != 'teacher':
        flash('Invalid teacher.')
        return redirect(url_for('admin_teachers'))
    db.session.delete(teacher)
    db.session.commit()
    flash('Teacher deleted successfully!')
    return redirect(url_for('admin_teachers'))

@app.route('/student')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('home'))
    doubts = Doubt.query.filter_by(student_id=session['user_id']).order_by(Doubt.created_at.desc()).all()
    return render_template('student.html', doubts=doubts)

# Doubt solving routes
@app.route('/doubts')
def doubts():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    role = session.get('role')
    if role == 'student':
        doubts = Doubt.query.filter_by(student_id=user_id).order_by(Doubt.created_at.desc()).all()
    elif role == 'teacher':
        doubts = Doubt.query.filter_by(teacher_id=user_id).order_by(Doubt.created_at.desc()).all()
    else:
        doubts = []
    return render_template('doubts.html', doubts=doubts)

@app.route('/doubts/submit', methods=['POST'])
def submit_doubt():
    if session.get('role') != 'student':
        return redirect(url_for('home'))
    question = request.form.get('question')
    if not question:
        flash('Question required.')
        return redirect(url_for('doubts'))
    doubt = Doubt(student_id=session['user_id'], question=question)
    db.session.add(doubt)
    db.session.commit()
    flash('Doubt submitted!')
    return redirect(url_for('doubts'))

@app.route('/doubts/answer/<int:doubt_id>', methods=['POST'])
def answer_doubt(doubt_id):
    if session.get('role') != 'teacher':
        return redirect(url_for('home'))
    answer = request.form.get('answer')
    doubt = Doubt.query.get_or_404(doubt_id)
    doubt.answer = answer
    doubt.status = 'answered'
    doubt.teacher_id = session['user_id']
    db.session.commit()
    flash('Doubt answered!')
    return redirect(url_for('doubts'))

@app.route('/doubts/close/<int:doubt_id>', methods=['POST'])
def close_doubt(doubt_id):
    doubt = Doubt.query.get_or_404(doubt_id)
    if session.get('role') == 'student' and doubt.student_id == session['user_id']:
        doubt.status = 'closed'
        db.session.commit()
        flash('Doubt closed!')
    return redirect(url_for('doubts'))


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out!')
    return redirect(url_for('home'))

# API route to handle classroom booking submission

@app.route('/book_classroom', methods=['POST'])
def book_classroom():
    if 'user_id' not in session:
        # Redirect to login page if not authenticated
        return redirect(url_for('login'))

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

    # Convert event_date to weekday name
    from datetime import datetime
    try:
        weekday = datetime.strptime(event_date, "%Y-%m-%d").strftime("%A")
    except Exception:
        weekday = event_date  # fallback if already weekday

    # Create timetable entry
    new_entry = Timetable(
        day=weekday,
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
        # Add demo users if not present
        from werkzeug.security import generate_password_hash
        demo_users = [
            {"username": "student@school.edu", "password": "student123", "role": "student"},
            {"username": "teacher@school.edu", "password": "teacher123", "role": "teacher"},
            {"username": "admin@school.edu", "password": "admin123", "role": "admin"},
            {"username": "admin001", "password": "SecureAdmin123", "role": "admin"}
        ]
        for user in demo_users:
            if not User.query.filter_by(username=user["username"]).first():
                new_user = User(
                    username=user["username"],
                    password=generate_password_hash(user["password"]),
                    role=user["role"]
                )
                db.session.add(new_user)
        db.session.commit()
    app.run(debug=True)
