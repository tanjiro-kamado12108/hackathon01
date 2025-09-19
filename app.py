'''
Smart Classroom & Timetable Scheduler

Opening & Problem Statement
Good morning everyone, respected judges and mentors. I am Shubham Dash. Today we are presenting our project: Smart Classroom and Timetable Scheduler.

Right now, making timetables in schools and colleges is:
- Very slow and mostly manual.
- Full of mistakes like overlapping classes or teachers getting extra load.
- Hard to change if a teacher is absent or a room is not available.
- Smart classrooms like labs and projectors are not used properly because there is no smart allocation.

In short, we are using old methods in today’s smart world.

Proposed Solution (Pratyush)
Good morning everyone, I am Pratyush. Now I will explain our proposed solution.

Our idea is to build an AI-powered Timetable Scheduler with Smart Classroom allocation.
It works in four simple steps:
1. Input – Admin enters subjects, teachers, students, and classrooms.
2. AI Scheduling – Our AI makes a clash-free timetable using smart algorithms.
3. Smart Allocation – The system automatically gives the right room, like a lab for practicals or a projector room for presentations.
4. Dynamic Updates – If a teacher is absent or a class gets cancelled, the timetable updates instantly and students/faculty get a notification.

Key Features
- No scheduling issues – No overlapping classes for students or teachers.
- Smart use of classrooms – Labs and projectors are used properly.
- Auto rescheduling – Quick updates if something changes.
- Dashboard – Shows classroom use and teacher workload.
- Easy access – Students and teachers can see their timetable on mobile or web.

Impact
This project will have a strong impact:
- Save 60–70% of admin time.
- Increase classroom usage by up to 40%.
- Remove last-minute confusion and timetable clashes.
- Provide clear and fair information to students, teachers, and management.

So, our Smart Classroom & Timetable Scheduler is not just a timetable tool – it is a smart system that saves time, reduces errors, and makes education smoother and smarter.
'''

from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__, template_folder='.')
app.secret_key = "supersecretkey"

# In-memory data stores
users = [
    {"id": 1, "username": "admin", "password": "adminpass", "role": "admin", "is_absent": False},
    {"id": 2, "username": "teacher1", "password": "teachpass", "role": "teacher", "is_absent": False},
    {"id": 3, "username": "student1", "password": "studpass", "role": "student", "is_absent": False},
]
timetable = []
notifications = []

# Helper functions

def get_user(username):
    for user in users:
        if user["username"] == username:
            return user
    return None

def add_notification(user_id, message):
    notifications.append({"user_id": user_id, "message": message, "read": False})

# Routes
@app.route('/')
def home():
    user = None
    if 'user_id' in session:
        user = next((u for u in users if u["id"] == session['user_id']), None)
    user_notifications = [n for n in notifications if user and n["user_id"] == user["id"] and not n["read"]]
    # Generate a simple timetable for demo
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
    return render_template('index.html', timetable=timetable, notifications=user_notifications)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user(username)
        if user and user["password"] == password:
            session['user_id'] = user["id"]
            session['role'] = user["role"]
            if user["role"] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user["role"] == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash("Invalid credentials")
    return render_template('signin.html')

@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    return render_template('admin panel.html', timetable=timetable, users=users)

@app.route('/admin/mark_absent', methods=['POST'])
def mark_teacher_absent():
    teacher_username = request.form.get('teacher_username')
    teacher = get_user(teacher_username)
    if teacher and teacher["role"] == "teacher":
        teacher["is_absent"] = True
        # Notify all students
        for student in users:
            if student["role"] == "student":
                add_notification(student["id"], f"Your teacher {teacher_username} is absent today.")
        flash(f"{teacher_username} marked as absent. Students notified.")
    else:
        flash("Teacher not found.")
    return redirect(url_for('admin_dashboard'))

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
        entries = [e for e in timetable if e["classroom"] == classroom and e["day"] == weekday]
        unavailable_slots = [e["period"] for e in entries]
    return render_template('class booking.html', unavailable_slots=unavailable_slots)

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
    new_entry = {
        "day": weekday,
        "period": time_slot,
        "subject": event_title,
        "teacher": teacher_name,
        "classroom": classroom_name
    }
    timetable.append(new_entry)

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

    # Try to find user by username or email, case-insensitive
    user = next((u for u in users if u["username"].lower() == username.lower()), None)
    if user and user["password"] == password:
        session['user_id'] = user["id"]
        session['role'] = user["role"]
        return jsonify({
            'success': True,
            'user': {
                'id': user["id"],
                'name': user["username"],
                'email': user["username"],
                'role': user["role"]
            }
        })
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/auth/status')
def api_auth_status():
    if 'user_id' in session:
        user = next((u for u in users if u["id"] == session['user_id']), None)
        if user:
            return jsonify({
                'authenticated': True,
                'user': {
                    'id': user["id"],
                    'name': user["username"],
                    'email': user["username"],
                    'role': user["role"]
                }
            })
    return jsonify({'authenticated': False}), 401


if __name__ == "__main__":
    app.run(debug=True)
