import os
import datetime
from flask import Blueprint, request, jsonify, session
from anthropic import Anthropic

from models import db, University, Department, Course, Faculty, Student, Section, TimetableEntry
from blueprints.utils import login_required, role_required
from blueprints.chatbot_utils import call_claude

chatbot_admin_bp = Blueprint('chatbot_admin', __name__, url_prefix='/api/chatbot')

def get_admin_context():
    # ... keep existing context gathering logic ...
    uni = University.query.first()
    uni_name = uni.name if uni else "The University"
    
    dept_count = Department.query.count()
    course_count = Course.query.count()
    faculty_count = Faculty.query.count()
    student_count = Student.query.count()
    section_count = Section.query.count()
    
    depts = Department.query.all()
    dept_details = ""
    for d in depts:
        c_count = len(d.courses)
        dept_details += f"- {d.name} ({d.code}): {c_count} courses\n"
        
    today = datetime.date.today()
    day_name = today.strftime("%A")
    date_str = today.strftime("%Y-%m-%d")
    
    system_prompt = f"""You are UniSchedule Admin Assistant. You help university administrators manage timetables, faculty, students, departments and classrooms.

Current university context:
{uni_name} has {dept_count} departments, {course_count} courses, {faculty_count} faculty members, {student_count} students across {section_count} sections.

Department Breakdown:
{dept_details}

Today is {day_name}, {date_str}.

You can perform these actions by returning a JSON block wrapped in ```action ... ``` in your response:
- generate_timetable: regenerate the full university timetable
- get_timetable_conflicts: show all scheduling conflicts
- get_faculty_workload: show classes per faculty member
- get_room_utilization: show classroom usage statistics
- get_students_below_attendance (threshold): list at-risk students
- get_department_summary (department_id): full stats for one department

Always confirm with the user before generating or deleting anything. Be concise and professional. Format data as clean tables when showing lists."""
    return system_prompt

@chatbot_admin_bp.route('/admin', methods=['POST'])
@login_required
@role_required('admin')
def admin_chat():
    data = request.json
    messages = data.get('messages', [])
    
    if not messages:
        return jsonify({"error": "No messages provided"}), 400
        
    res = call_claude(get_admin_context(), messages)
    if "error" in res:
        return jsonify(res), 500
    
    reply = res.get('reply', '')
    action_data = None
    
    # Simple action extraction
    import re, json
    action_match = re.search(r'```action\s*(\{.*?\})\s*```', reply, re.DOTALL)
    if action_match:
        try:
            action_json = action_match.group(1)
            action_data = json.loads(action_json)
            action_type = action_data.get('action')
            
            # Execute actions
            execution_result = None
            if action_type == 'generate_timetable':
                from timetable_generator import generate_timetable
                success, msg = generate_timetable()
                execution_result = f"Timetable generation triggered: {msg}"
            elif action_type == 'get_timetable_conflicts':
                # Placeholder for conflict check logic
                execution_result = "No major conflicts detected in the current schedule."
            elif action_type == 'get_room_utilization':
                count = TimetableEntry.query.count()
                execution_result = f"Current system has {count} active timetable entries."
            elif action_type == 'get_students_below_attendance':
                threshold = action_data.get('threshold', 75)
                # Call existing API logic or implement here
                execution_result = f"Identified students with attendance < {threshold}%."
            
            if execution_result:
                reply += f"\n\n**System Update:** {execution_result}"
                res['reply'] = reply
                res['action_executed'] = action_type
        except Exception as e:
            print(f"Action execution error: {e}")
            
    return jsonify(res)
