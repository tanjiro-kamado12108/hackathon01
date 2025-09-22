from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify

app = Flask(__name__)  # Default template folder is 'templates'
app.secret_key = "supersecretkey"

# In-memory data
users = [
    {"id": 1, "username": "admin", "password": "adminpass", "role": "admin", "is_absent": False},
    {"id": 2, "username": "teacher1", "password": "teachpass", "role": "teacher", "is_absent": False},
    {"id": 3, "username": "student1", "password": "studpass", "role": "student", "is_absent": False},
]
timetable = []
notifications = []
messages = []

# ----------------- Helpers -----------------
def get_user(username):
    for user in users:
        if user["username"] == username:
            return user
    return None

def get_user_by_id(user_id):
    for user in users:
        if user["id"] == user_id:
            return user
    return None

def add_notification(user_id, message):
    notifications.append({"user_id": user_id, "message": message, "read": False})

def send_message(sender_id, receiver_id, message_text):
    from datetime import datetime
    message_id = len(messages) + 1
    timestamp = datetime.now().isoformat()
    message = {
        "id": message_id,
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "message": message_text,
        "read": False,
        "timestamp": timestamp
    }
    messages.append(message)
    return message

def get_messages_for_user(user_id):
    return [msg for msg in messages if msg["receiver_id"] == user_id]

def mark_message_as_read(message_id):
    for msg in messages:
        if msg["id"] == message_id:
            msg["read"] = True
            return True
    return False

# ----------------- ROUTES -----------------
@app.route('/')
def home():
    user = None
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
    user_notifications = [n for n in notifications if user and n["user_id"] == user["id"] and not n["read"]]

    # Demo timetable
    global timetable
    if not timetable:
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        times = ['08:00', '10:00', '12:00', '14:00', '16:00']
        subjects = ['Math', 'Science', 'English', 'History', 'Art', 'PE', 'Music']
        teachers = [u["username"] for u in users if u["role"] == "teacher"]
        for day in days:
            for time in times:
                timetable.append({
                    "day": day,
                    "period": time,
                    "subject": subjects[(hash(day+time) % len(subjects))],
                    "teacher": teachers[(hash(day+time) % len(teachers))],
                    "classroom": f"Room {((hash(day+time) % 10) + 1)}"
                })

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
    user_notifications = [n for n in notifications if n["user_id"] == user["id"] and not n["read"]]
    return render_template('student.html', user=user, notifications=user_notifications)

@app.route('/teacher_dashboard')
def teacher_dashboard():
    if session.get('role') != 'teacher':
        return redirect(url_for('home'))
    user = get_user_by_id(session['user_id'])
    user_notifications = [n for n in notifications if n["user_id"] == user["id"] and not n["read"]]
    return render_template('teacher.html', user=user, notifications=user_notifications)

@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    return render_template('admin_panel.html', timetable=timetable, users=users)

# ----------------- RUN APP -----------------
if __name__ == "__main__":
    app.run(debug=True, port=5001)
