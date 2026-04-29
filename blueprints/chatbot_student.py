import os
import datetime
from flask import Blueprint, request, jsonify, session
from sqlalchemy import func

from models import db, Student, Section, Course, TimetableEntry, Attendance, Faculty
from blueprints.utils import login_required, role_required
from blueprints.chatbot_utils import call_claude, format_timetable_for_prompt, format_attendance_for_prompt

chatbot_student_bp = Blueprint('chatbot_student', __name__, url_prefix='/api/chatbot')

def get_student_context(student_id):
    student = Student.query.get(student_id)
    if not student:
        return "Student not found."
    
    section = student.sections[0] if student.sections else None
    section_name = section.name if section else "N/A"
    section_id = section.id if section else None
    dept_name = student.department.name if student.department else "N/A"
    
    # Enrolled courses
    courses = student.courses
    course_data = []
    attendance_data = []
    low_attendance_subjects = []
    
    for c in courses:
        # Faculty for this course in this section
        entry = TimetableEntry.query.filter_by(section_id=section_id, course_id=c.id).first() if section_id else None
        faculty_name = entry.faculty.name if (entry and entry.faculty) else "TBD"
        room = entry.classroom.room_number if (entry and entry.classroom) else "TBD"
        course_data.append(f"- {c.name} ({c.code}): {faculty_name}, {c.credits} credits, {c.difficulty} difficulty, Room {room}")
        
        # Attendance
        total_records = Attendance.query.filter_by(student_id=student.id, course_id=c.id).count()
        present_count = Attendance.query.filter_by(student_id=student.id, course_id=c.id, status='present').count()
        percent = (present_count / total_records * 100) if total_records > 0 else 0
        held = db.session.query(func.count(func.distinct(Attendance.date))).filter_by(course_id=c.id).scalar() or 0
        
        att_item = {"course": c.code, "percent": percent, "held": held}
        attendance_data.append(att_item)
        if percent < 75:
            low_attendance_subjects.append(c.code)

    course_list = "\n".join(course_data)
    attendance_summary = format_attendance_for_prompt(attendance_data)
    low_att_list = ", ".join(low_attendance_subjects) if low_attendance_subjects else "None"
    
    # Timetable
    today_name = datetime.date.today().strftime("%A")
    all_entries = TimetableEntry.query.filter_by(section_id=section_id).all() if section_id else []
    today_entries = [e for e in all_entries if e.day == today_name]
    today_schedule = format_timetable_for_prompt(today_entries)
    
    now_time = datetime.datetime.now().strftime("%H:%M")

    system_prompt = f"""You are UniSchedule Student Assistant. You help {student.name} from section {section_name} ({dept_name}) stay on top of their academic schedule.

Enrolled courses:
{course_list}

Today is {today_name} at {now_time}. Today's classes:
{today_schedule}

Attendance summary:
{attendance_summary}

Subjects needing attention (below 75%): {low_att_list}

You can help with:
- Showing timetable for any day or the full week
- Checking attendance percentage per subject
- Telling what the next upcoming class is based on current time
- Explaining which subjects need more attendance urgently
- Answering questions about courses, faculty, classroom locations

You can suggest navigating to specific dashboard pages by returning a JSON block wrapped in ```action ... ``` in your response:
- {"action": "get_my_timetable"}
- {"action": "get_attendance_report"}
- {"action": "get_next_class"}
- {"action": "get_course_details"}
- {"action": "get_low_attendance_alert"}

You are strictly READ ONLY. Never attempt to modify any data.
Be friendly, encouraging and supportive. If a student is stressed about attendance, be empathetic and suggest practical steps. Keep responses concise. Use tables for schedule data. Add motivational notes when relevant.

IMPORTANT: If any subject is below 75% attendance, proactively mention it in your first response to remind the student to attend those classes."""
    return system_prompt

@chatbot_student_bp.route('/student', methods=['POST'])
@login_required
@role_required('student')
def student_chat():
    data = request.json
    messages = data.get('messages', [])
    student_id = session.get('user_id')
    
    if not messages:
        return jsonify({"error": "No messages"}), 400
        
    res = call_claude(get_student_context(student_id), messages)
    if "error" in res:
        return jsonify(res), 500
    return jsonify(res)
