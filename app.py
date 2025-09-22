from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__, template_folder='.')  # Look for templates in current directory
app.secret_key = "supersecretkey"

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'instance')
os.makedirs(db_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(db_path, 'school.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    is_absent = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<User {self.username}>'

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Timetable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(20), nullable=False)
    period = db.Column(db.String(10), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    teacher = db.Column(db.String(80), nullable=False)
    classroom = db.Column(db.String(20), nullable=False)

# Initialize database tables and sample data
with app.app_context():
    db.create_all()
    # Create default users if they don't exist
    if not User.query.first():
        admin = User(username="admin", password="adminpass", role="admin", is_absent=False)
        teacher = User(username="teacher1", password="teachpass", role="teacher", is_absent=False)
        student = User(username="student1", password="studpass", role="student", is_absent=False)
        db.session.add(admin)
        db.session.add(teacher)
        db.session.add(student)
        db.session.commit()

        # Create sample timetable
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        times = ['08:00', '10:00', '12:00', '14:00', '16:00']
        subjects = ['Math', 'Science', 'English', 'History', 'Art', 'PE', 'Music']

        for day in days:
            for time in times:
                timetable_entry = Timetable(
                    day=day,
                    period=time,
                    subject=subjects[(hash(day+time) % len(subjects))],
                    teacher=teacher.username,
                    classroom=f"Room {((hash(day+time) % 10) + 1)}"
                )
                db.session.add(timetable_entry)
        db.session.commit()

# ----------------- Helpers -----------------
def get_user(username):
    return User.query.filter_by(username=username).first()

def get_user_by_id(user_id):
    return User.query.get(user_id)

def add_notification(user_id, message):
    notif = Notification(user_id=user_id, message=message, read=False)
    db.session.add(notif)
    db.session.commit()

def send_message(sender_id, receiver_id, message_text):
    message = Message(sender_id=sender_id, receiver_id=receiver_id, message=message_text, read=False)
    db.session.add(message)
    db.session.commit()
    return message

def get_messages_for_user(user_id):
    return Message.query.filter_by(receiver_id=user_id).all()

def mark_message_as_read(message_id):
    msg = Message.query.get(message_id)
    if msg:
        msg.read = True
        db.session.commit()
        return True
    return False

# ----------------- ROUTES -----------------
@app.route('/')
def home():
    user = None
    user_notifications = []
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
        user_notifications = Notification.query.filter_by(user_id=user.id, read=False).all()

    # Demo timetable
    timetable = Timetable.query.limit(30).all()

    classes = timetable[:5]
    backlog_classes = [
        {"subject": "Advanced Mathematics", "date": "2024-12-15"},
        {"subject": "Physics Lab", "date": "2024-12-16"},
        {"subject": "Chemistry", "date": "2024-12-17"},
        {"subject": "English Literature", "date": "2024-12-18"},
        {"subject": "Computer Science", "date": "2024-12-19"}
    ]

    rooms = [
        {"name": "Room 101", "available": True},
        {"name": "Room 102", "available": False},
        {"name": "Room 103", "available": True},
        {"name": "Room 104", "available": True},
        {"name": "Lab 201", "available": False},
        {"name": "Lab 202", "available": True},
        {"name": "Auditorium", "available": False},
        {"name": "Library", "available": True}
    ]

    return render_template('index.html',
                           classes=classes,
                           notifications=user_notifications,
                           backlog_classes=backlog_classes,
                           rooms=rooms)

# ----------------- Dashboards -----------------
@app.route('/student_dashboard')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('home'))
    user = get_user_by_id(session['user_id'])
    user_notifications = Notification.query.filter_by(user_id=user.id, read=False).all()
    return render_template('student.html', user=user, notifications=user_notifications)

@app.route('/teacher_dashboard')
def teacher_dashboard():
    if session.get('role') != 'teacher':
        return redirect(url_for('home'))
    user = get_user_by_id(session['user_id'])
    user_notifications = Notification.query.filter_by(user_id=user.id, read=False).all()
    return render_template('teacher.html', user=user, notifications=user_notifications)

@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    timetable = Timetable.query.limit(30).all()
    users = User.query.all()
    return render_template('admin_panel.html', timetable=timetable, users=users)

# ----------------- RUN APP -----------------
if __name__ == "__main__":
    app.run(debug=True, port=5001)