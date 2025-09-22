'''
Smart Classroom & Timetable Scheduler

Opening & Problem Statement
Good morning everyone, respected judges and mentors. I am Shubham Dash. Today we are presenting our project: Smart Classroom and Timetable Scheduler.

Right now, making timetables in schools and colleges is:
- Very slow and mostly manual.
- Full of mistakes like overlapping classes or teachers getting extra load.
- Hard to change if a teacher is absent or a room is not available.
- Smart classrooms like labs and projectors are not used properly because there is no smart allocation.

In short, we are using old methods in today's smart world.

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

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify

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

# Demo credentials for sign-in (update to match backend users)
# Student: student1 / studpass
# Teacher: teacher1 / teachpass
# Admin: admin / adminpass
# You can also sign up new users via the signup page.

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

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'student')
        if not username or not password:
            flash('All fields are required')
            return redirect(url_for('signup'))
        if get_user(username):
            flash('Username already exists')
            return redirect(url_for('signup'))
        new_id = max([u['id'] for u in users]) + 1 if users else 1
        users.append({"id": new_id, "username": username, "password": password, "role": role, "is_absent": False})
        flash('Account created successfully! Please log in.')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/student_dashboard')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('home'))
    user = next((u for u in users if u["id"] == session['user_id']), None)
    user_notifications = [n for n in notifications if user and n["user_id"] == user["id"] and not n["read"]]
    return render_template('student.html', user=user, notifications=user_notifications)

@app.route('/teacher_dashboard')
def teacher_dashboard():
    if session.get('role') != 'teacher':
        return redirect(url_for('home'))
    user = next((u for u in users if u["id"] == session['user_id']), None)
    user_notifications = [n for n in notifications if user and n["user_id"] == user["id"] and not n["read"]]
    return render_template('teacher.html', user=user, notifications=user_notifications)

@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    return render_template('admin panel.html', timetable=timetable, users=users)

@app.route('/admin_teachers')
def admin_teachers():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    # For demo, show all teachers
    teacher_list = [u for u in users if u['role'] == 'teacher']
    return render_template('manageteachers.html', teachers=teacher_list)

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

@app.route('/book_classroom', methods=['POST'])
def book_classroom():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    data = request.get_json()
    if not data:
        flash('Invalid request')
        return redirect(url_for('home'))
    # Extract booking details
    user_id = session['user_id']
    event_title = data.get('eventTitle')
    event_date = data.get('eventDate')
    time_slot = data.get('timeSlot')
    duration = data.get('duration')
    classroom_name = data.get('classroom', {}).get('name')
    teacher_name = data.get('classroom', {}).get('type')
    description = data.get('description')
    equipment = data.get('equipment', [])
    if not all([event_title, event_date, time_slot, duration, classroom_name]):
        flash('Missing required booking information')
        return redirect(url_for('home'))
    from datetime import datetime
    try:
        weekday = datetime.strptime(event_date, "%Y-%m-%d").strftime("%A")
    except Exception:
        weekday = event_date
    new_entry = {
        "day": weekday,
        "period": time_slot,
        "subject": event_title,
        "teacher": teacher_name,
        "classroom": classroom_name
    }
    timetable.append(new_entry)
    flash('Classroom booked successfully!')
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('home'))

@app.route('/settings')
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('settings.html')

@app.route('/classreport')
def classreport():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('classreport.html')

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

# API Routes for Student Dashboard
@app.route('/api/auth/status')
def api_auth_status():
    if 'user_id' in session:
        user = next((u for u in users if u["id"] == session['user_id']), None)
        if user:
            return jsonify({
                'authenticated': True,
                'user': {
                    'id': user['id'],
                    'name': user['username'],
                    'email': f"{user['username']}@school.edu",
                    'role': user['role']
                }
            })
    return jsonify({'authenticated': False}), 401

@app.route('/api/student/assignments')
def api_student_assignments():
    if session.get('role') != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Mock assignments data
    assignments = [
        {
            'id': 1,
            'title': 'Mathematics Quiz',
            'due_date': '2024-12-20T23:59:00',
            'course': 'Mathematics'
        },
        {
            'id': 2,
            'title': 'History Essay',
            'due_date': '2024-12-22T23:59:00',
            'course': 'History'
        },
        {
            'id': 3,
            'title': 'Science Lab Report',
            'due_date': '2024-12-25T23:59:00',
            'course': 'Science'
        }
    ]
    return jsonify(assignments)

@app.route('/api/student/courses')
def api_student_courses():
    if session.get('role') != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Mock courses data
    courses = [
        {
            'id': 1,
            'name': 'Mathematics',
            'teacher_name': 'Mrs. Johnson',
            'progress': 75
        },
        {
            'id': 2,
            'name': 'Science',
            'teacher_name': 'Dr. Smith',
            'progress': 60
        },
        {
            'id': 3,
            'name': 'History',
            'teacher_name': 'Mr. Davis',
            'progress': 85
        },
        {
            'id': 4,
            'name': 'English',
            'teacher_name': 'Ms. Wilson',
            'progress': 90
        }
    ]
    return jsonify(courses)

@app.route('/api/student/stats')
def api_student_stats():
    if session.get('role') != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Mock stats data
    stats = {
        'completed_assignments': 12,
        'pending_assignments': 5,
        'average_grade': 87,
        'total_courses': 6
    }
    return jsonify(stats)

@app.route('/api/student/schedule')
def api_student_schedule():
    if session.get('role') != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Mock schedule data
    schedule = [
        {
            'id': 1,
            'title': 'Mathematics',
            'start_time': '2024-12-19T09:00:00',
            'location': 'Room 101'
        },
        {
            'id': 2,
            'title': 'Science',
            'start_time': '2024-12-19T10:30:00',
            'location': 'Lab 205'
        },
        {
            'id': 3,
            'title': 'History',
            'start_time': '2024-12-19T13:00:00',
            'location': 'Room 203'
        },
        {
            'id': 4,
            'title': 'English',
            'start_time': '2024-12-19T14:30:00',
            'location': 'Room 105'
        }
    ]
    return jsonify(schedule)

@app.route('/api/student/announcements')
def api_student_announcements():
    if session.get('role') != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Mock announcements data
    announcements = [
        {
            'id': 1,
            'title': 'Library Hours Extended',
            'content': 'The library will be open until 10 PM during exam week.',
            'created_at': '2024-12-19T10:00:00'
        },
        {
            'id': 2,
            'title': 'Exam Schedule Released',
            'content': 'Final exam schedules are now available in your student portal.',
            'created_at': '2024-12-18T14:30:00'
        }
    ]
    return jsonify(announcements)

if __name__ == "__main__":
    app.run(debug=True)
