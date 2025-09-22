from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify

app = Flask(__name__, template_folder='.')  # Look for templates in current directory
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

    # AI-Generated Enhanced Timetable
    global timetable
    if not timetable:
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        times = ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00']

        # Enhanced subjects with more variety and detail
        subjects = [
            'Advanced Mathematics', 'Applied Physics', 'Organic Chemistry', 'World Literature',
            'Computer Science', 'Data Structures', 'Web Development', 'Mobile App Dev',
            'English Composition', 'Creative Writing', 'Public Speaking', 'Business English',
            'World History', 'Ancient Civilizations', 'Modern Politics', 'Economics',
            'Biology', 'Environmental Science', 'Genetics', 'Neuroscience',
            'Physical Education', 'Team Sports', 'Yoga & Wellness', 'Swimming',
            'Visual Arts', 'Digital Design', 'Photography', 'Sculpture',
            'Music Theory', 'Jazz Ensemble', 'Piano', 'Guitar',
            'Psychology', 'Sociology', 'Philosophy', 'Ethics',
            'Statistics', 'Machine Learning', 'Database Systems', 'Network Security'
        ]

        # Teacher assignments with subjects they specialize in
        teachers_subjects = {
            'teacher1': ['Advanced Mathematics', 'Statistics', 'Machine Learning'],
            'admin': ['Computer Science', 'Database Systems', 'Network Security']
        }

        # Generate additional teachers for more variety
        additional_teachers = ['Dr. Smith', 'Prof. Johnson', 'Ms. Davis', 'Mr. Wilson', 'Dr. Brown']
        all_teachers = [u["username"] for u in users if u["role"] == "teacher"] + additional_teachers

        # Classrooms with different types and capacities
        classrooms = [
            'Room 101 (Lecture Hall)', 'Room 102 (Lab)', 'Room 103 (Seminar)',
            'Room 201 (Studio)', 'Room 202 (Gym)', 'Room 203 (Auditorium)',
            'Lab 301 (Computer)', 'Lab 302 (Science)', 'Lab 303 (Chemistry)',
            'Studio 401 (Art)', 'Studio 402 (Music)', 'Conference 501'
        ]

        # Generate timetable with AI-like logic
        import random
        random.seed(42)  # For consistent results

        for day in days:
            for time in times:
                # Skip some slots to make it more realistic (breaks, free periods)
                if random.random() < 0.2:  # 20% chance of free period
                    continue

                # Select subject based on time of day and day of week
                if time in ['08:00', '09:00'] and day in ['Monday', 'Wednesday', 'Friday']:
                    # Morning core subjects
                    subject_pool = [s for s in subjects if any(core in s.lower() for core in ['math', 'english', 'science'])]
                elif time in ['14:00', '15:00', '16:00'] and day in ['Tuesday', 'Thursday']:
                    # Afternoon electives
                    subject_pool = [s for s in subjects if any(elective in s.lower() for elective in ['art', 'music', 'pe', 'psychology'])]
                else:
                    subject_pool = subjects

                subject = random.choice(subject_pool)

                # Assign teacher based on subject expertise
                if subject in teachers_subjects.get('teacher1', []):
                    teacher = 'teacher1'
                elif subject in teachers_subjects.get('admin', []):
                    teacher = 'admin'
                else:
                    teacher = random.choice(all_teachers)

                classroom = random.choice(classrooms)

                timetable.append({
                    "day": day,
                    "period": time,
                    "subject": subject,
                    "teacher": teacher,
                    "classroom": classroom,
                    "duration": "60 min",
                    "capacity": random.randint(15, 40)
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
