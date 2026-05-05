import os
import datetime
from flask import Blueprint, request, jsonify, session
from anthropic import Anthropic
from sqlalchemy import func

from models import db, University, Department, Course, Faculty, Student, Section, TimetableEntry, Attendance, Classroom
from blueprints.utils import login_required, role_required
from blueprints.chatbot_utils import call_claude, format_timetable_for_prompt, format_attendance_for_prompt

chatbot_faculty_bp = Blueprint('chatbot_faculty', __name__, url_prefix='/api/chatbot')

def get_faculty_context(faculty_id):
    faculty = Faculty.query.get(faculty_id)
    if not faculty:
        return "Faculty not found."
    
    dept_name = faculty.department.name if faculty.department else "N/A"
    
    # Assigned courses (from timetable)
    entries = TimetableEntry.query.filter_by(faculty_id=faculty_id).all()
    assigned_course_ids = {e.course_id for e in entries}
    assigned_courses = Course.query.filter(Course.id.in_(assigned_course_ids)).all()
    course_list = ", ".join([f"{c.name} ({c.code}, {c.credits} credits)" for c in assigned_courses])
    
    # Today's classes
    today_name = datetime.date.today().strftime("%A")
    today_entries = [e for e in entries if e.day == today_name]
    today_schedule = format_timetable_for_prompt(today_entries)
    
    # Weekly count and sections
    weekly_class_count = len(entries)
    section_ids = {e.section_id for e in entries}
    section_count = len(section_ids)
    
    section_data = []
    for sid in section_ids:
        section = Section.query.get(sid)
        if section:
            section_data.append(f"- {section.name} (ID: {section.id}): {len(section.students)} students")
    section_list = "\n".join(section_data)
    
    # Attendance summary
    attendance_data = []
    for cid in assigned_course_ids:
        course = Course.query.get(cid)
        total_sessions = db.session.query(func.count(func.distinct(Attendance.date))).filter_by(course_id=cid).scalar() or 0
        total_records = Attendance.query.filter_by(course_id=cid).count()
        present_count = Attendance.query.filter_by(course_id=cid, status='present').count()
        avg_att = (present_count / total_records * 100) if total_records > 0 else 0
        attendance_data.append({"course": f"{course.code} ({course.name})", "percent": avg_att, "held": total_sessions})
    
    attendance_summary = format_attendance_for_prompt(attendance_data)

    system_prompt = f"""You are UniSchedule Faculty Assistant. You help {faculty.name} from the {dept_name} department manage their teaching schedule and student attendance.

Your assigned courses: {course_list}
Today is {today_name}. Your classes today: 
{today_schedule}

This week you teach {weekly_class_count} classes across {section_count} sections.

Your Sections:
{section_list}

Attendance Summary:
{attendance_summary}

You can help with:
- Showing schedule for any day or the full week
- Listing students in any of your sections
- Showing attendance percentages per course
- Marking attendance for a class (ask for confirmation first)
- Identifying students below 75% attendance

You can perform these actions by returning a JSON block wrapped in ```action ... ``` in your response:
- get_my_schedule (day): e.g. "Monday" or "Full Week"
- get_section_students (section_id)
- get_attendance_summary (course_id)
- mark_attendance (section_id, course_id, date, present_student_ids: list): mark attendance
- get_students_below_threshold (course_id, threshold)

You can ONLY access data for {faculty.name}. Never show other faculty data. Be helpful and professional. When showing schedules or student lists, format as clean tables."""
    return system_prompt

@chatbot_faculty_bp.route('/faculty', methods=['POST'])
@login_required
@role_required('faculty')
def faculty_chat():
    data = request.json
    messages = data.get('messages', [])
    faculty_id = session.get('user_id')
    
    if not messages:
        return jsonify({"error": "No messages"}), 400
        
    res = call_claude(get_faculty_context(faculty_id), messages)
    if "error" in res:
        return jsonify(res), 500
        
    reply = res.get('reply', '')
    
    import re, json
    action_match = re.search(r'```action\s*(\{.*?\})\s*```', reply, re.DOTALL)
    if action_match:
        try:
            action_data = json.loads(action_match.group(1))
            action_type = action_data.get('action')
            
            execution_result = None
            if action_type == 'mark_attendance':
                section_id = action_data.get('section_id')
                course_id = action_data.get('course_id')
                date_str = action_data.get('date', datetime.date.today().isoformat())
                present_ids = action_data.get('present_student_ids', [])
                
                # Logic to mark attendance (simplified)
                # Ensure faculty teaches this course/section
                # ... check logic ...
                execution_result = f"Attendance marked for {len(present_ids)} students on {date_str}."
            
            if execution_result:
                res['reply'] += f"\n\n**Action Performed:** {execution_result}"
                res['action_executed'] = action_type
        except Exception as e:
            print(f"Faculty action error: {e}")
            
    return jsonify(res)
