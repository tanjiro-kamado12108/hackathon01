
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
messages = []

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

def get_user_by_id(user_id):
    """Get user by ID"""
    for user in users:
        if user["id"] == user_id:
            return user
    return None

def send_message(sender_id, receiver_id, message_text):
    """Send a message from sender to receiver"""
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
    """Get all messages for a specific user"""
    return [msg for msg in messages if msg["receiver_id"] == user_id]

def mark_message_as_read(message_id):
    """Mark a message as read"""
    for msg in messages:
        if msg["id"] == message_id:
            msg["read"] = True
            return True
    return False

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

    # Prepare data for template
    classes = timetable[:5]  # Show first 5 classes for demo
    backlog_classes = [
        {"subject": "Advanced Mathematics", "date": "2024-12-15"},
        {"subject": "Physics Lab", "date": "2024-12-16"},
        {"subject": "Chemistry", "date": "2024-12-17"},
        {"subject": "English Literature", "date": "2024-12-18"},
        {"subject": "Computer Science", "date": "2024-12-19"}
    ]

    # Generate room availability data
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

@app.route('/assignment')
def assignment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('assignment.html')

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

# Messaging API Routes
@app.route('/api/student/send_message', methods=['POST'])
def api_send_message():
    """API endpoint for students to send messages to teachers"""
    if session.get('role') != 'student':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400

    receiver_id = data.get('receiver_id')
    message_text = data.get('message')

    if not receiver_id or not message_text:
        return jsonify({'error': 'Missing receiver_id or message'}), 400

    # Verify receiver is a teacher
    receiver = get_user_by_id(receiver_id)
    if not receiver or receiver['role'] != 'teacher':
        return jsonify({'error': 'Invalid receiver'}), 400

    sender_id = session['user_id']

    # Send the message
    message = send_message(sender_id, receiver_id, message_text)

    # Create notification for the teacher
    add_notification(receiver_id, f"New message from {get_user_by_id(sender_id)['username']}")

    return jsonify({
        'success': True,
        'message': 'Message sent successfully',
        'message_id': message['id']
    })

@app.route('/api/teacher/messages')
def api_teacher_messages():
    """API endpoint for teachers to get their messages"""
    if session.get('role') != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403

    user_id = session['user_id']
    messages_list = get_messages_for_user(user_id)

    # Format messages for response
    formatted_messages = []
    for msg in messages_list:
        sender = get_user_by_id(msg['sender_id'])
        formatted_messages.append({
            'id': msg['id'],
            'sender_name': sender['username'] if sender else 'Unknown',
            'sender_id': msg['sender_id'],
            'message': msg['message'],
            'read': msg['read'],
            'timestamp': msg['timestamp']
        })

    # Sort by timestamp (newest first)
    formatted_messages.sort(key=lambda x: x['timestamp'], reverse=True)

    return jsonify(formatted_messages)

@app.route('/api/teacher/mark_message_read', methods=['POST'])
def api_mark_message_read():
    """API endpoint for teachers to mark messages as read"""
    if session.get('role') != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400

    message_id = data.get('message_id')
    if not message_id:
        return jsonify({'error': 'Missing message_id'}), 400

    success = mark_message_as_read(message_id)
    if success:
        return jsonify({'success': True, 'message': 'Message marked as read'})
    else:
        return jsonify({'error': 'Message not found'}), 404

@app.route('/api/student/teachers')
def api_get_teachers():
    """API endpoint to get list of teachers for student messaging"""
    if session.get('role') != 'student':
        return jsonify({'error': 'Unauthorized'}), 403

    teachers = [user for user in users if user['role'] == 'teacher']
    formatted_teachers = []
    for teacher in teachers:
        formatted_teachers.append({
            'id': teacher['id'],
            'name': teacher['username'],
            'email': f"{teacher['username']}@school.edu"
        })

    return jsonify(formatted_teachers)

# Teacher Messaging API Routes
@app.route('/api/teacher/students')
def api_teacher_students():
    """API endpoint for teachers to get list of students"""
    if session.get('role') != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403

    students = [user for user in users if user['role'] == 'student']
    formatted_students = []
    for student in students:
        # Get unread message count for this student
        unread_count = len([msg for msg in messages
                           if msg['sender_id'] == student['id'] and
                           msg['receiver_id'] == session['user_id'] and
                           not msg['read']])

        formatted_students.append({
            'id': student['id'],
            'name': student['username'],
            'class': 'General',  # Default class for demo
            'unread': unread_count,
            'online': True  # For demo purposes
        })

    return jsonify(formatted_students)

@app.route('/api/teacher/messages')
def api_teacher_student_messages():
    """API endpoint for teachers to get messages with a specific student"""
    if session.get('role') != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403

    student_id = request.args.get('student_id', type=int)
    if not student_id:
        return jsonify({'error': 'Missing student_id parameter'}), 400

    # Get messages between teacher and this student
    teacher_id = session['user_id']
    conversation_messages = [msg for msg in messages
                           if ((msg['sender_id'] == teacher_id and msg['receiver_id'] == student_id) or
                               (msg['sender_id'] == student_id and msg['receiver_id'] == teacher_id))]

    # Format messages for response
    formatted_messages = []
    for msg in conversation_messages:
        sender = get_user_by_id(msg['sender_id'])
        formatted_messages.append({
            'id': msg['id'],
            'sender': 'teacher' if msg['sender_id'] == teacher_id else 'student',
            'content': msg['message'],
            'timestamp': msg['timestamp'],
            'read': msg['read']
        })

    # Sort by timestamp (oldest first for conversation flow)
    formatted_messages.sort(key=lambda x: x['timestamp'])

    return jsonify(formatted_messages)

@app.route('/api/teacher/send_message', methods=['POST'])
def api_teacher_send_message():
    """API endpoint for teachers to send messages to students"""
    if session.get('role') != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400

    student_id = data.get('student_id')
    message_text = data.get('content')

    if not student_id or not message_text:
        return jsonify({'error': 'Missing student_id or content'}), 400

    # Verify student exists
    student = get_user_by_id(student_id)
    if not student or student['role'] != 'student':
        return jsonify({'error': 'Invalid student'}), 400

    teacher_id = session['user_id']

    # Send the message
    message = send_message(teacher_id, student_id, message_text)

    # Create notification for the student
    add_notification(student_id, f"New message from {get_user_by_id(teacher_id)['username']}")

    return jsonify({
        'success': True,
        'message': 'Message sent successfully',
        'message_id': message['id']
    })

@app.route('/api/teacher/mark_message_read', methods=['POST'])
def api_teacher_mark_message_read():
    """API endpoint for teachers to mark messages as read"""
    if session.get('role') != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400

    student_id = data.get('student_id')
    if not student_id:
        return jsonify({'error': 'Missing student_id'}), 400

    teacher_id = session['user_id']

    # Mark all messages from this student as read
    updated_count = 0
    for msg in messages:
        if msg['sender_id'] == student_id and msg['receiver_id'] == teacher_id and not msg['read']:
            msg['read'] = True
            updated_count += 1

    return jsonify({
        'success': True,
        'message': f'Marked {updated_count} messages as read'
    })

if __name__ == "__main__":
    app.run(debug=True, port=5001)
