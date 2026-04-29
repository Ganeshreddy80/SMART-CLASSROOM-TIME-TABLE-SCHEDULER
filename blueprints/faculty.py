"""
Faculty blueprint — faculty dashboard and timetable pages.
"""
from flask import Blueprint, render_template, request, session
import json

from models import (Faculty, Student, Section, Course, TimetableEntry)
from blueprints.utils import login_required, role_required

faculty_bp = Blueprint('faculty_bp', __name__)


@faculty_bp.route('/faculty-app')
@login_required
@role_required('faculty', 'admin')
def faculty_app():
    faculties = Faculty.query.all()
    faculty_list = []
    for f in faculties:
        assigned_secs = []
        for t in f.timetable_entries:
            if t.section.id not in assigned_secs:
                assigned_secs.append(t.section.id)

        faculty_list.append({
            "id": f.faculty_uid,
            "name": f.name,
            "email": f.email,
            "dept": f.department.code if f.department else "",
            "designation": "Assistant Professor",
            "specialization": "Specialization",
            "phone": "+91 00000 00000",
            "cabinNo": "Faculty Cabin",
            "joiningDate": "01 Jan 2020",
            "experience": "5 years",
            "canTeach": [c.code for c in f.courses_can_teach],
            "assignedSections": assigned_secs,
            "password": "password",  # dummy — never used for auth
            "photo": f.photo_url or None
        })

    sections_list = []
    sections = Section.query.all()
    for s in sections:
        sections_list.append({
            "id": s.id,
            "name": s.name,
            "dept": s.department.code if s.department else "",
            "semester": 4,
            "year": 2,
            "courses": list(set([t.course.code for t in s.timetable_entries])),
            "students": [st.student_uid for st in s.students]
        })

    students_list = []
    students = Student.query.all()
    for s in students:
        sec = s.sections[0] if s.sections else None
        students_list.append({
            "id": s.student_uid,
            "regNo": s.student_uid,
            "name": s.name,
            "section": sec.id if sec else None,
            "email": s.email,
            "dept": s.department.code if s.department else "",
            "semester": 4,
            "year": 2,
            "phone": "+91 00000 00000",
            "dob": "01 Jan 2005",
            "blood": "O+",
            "hostel": "Day Scholar",
            "advisor": "Faculty",
            "cgpa": 8.5,
            "photo": s.photo_url or None
        })

    courses_list = []
    courses = Course.query.all()
    for c in courses:
        courses_list.append({
            "code": c.code,
            "name": c.name,
            "dept": c.department.code if c.department else "",
            "credits": c.credits,
            "type": c.course_type
        })

    timetable_list = []
    entries = TimetableEntry.query.all()
    for t in entries:
        slot_str = t.timeslot
        parts = slot_str.split('-')
        if len(parts) == 2:
            s1 = parts[0].split(':')[0]
            s2 = parts[1].split(':')[0]
            slot_str = f"{s1}-{s2}"

        timetable_list.append({
            "section": t.section.id if t.section else "",
            "day": t.day[:3],
            "slot": slot_str,
            "course": t.course.code if t.course else "",
            "faculty": t.faculty.faculty_uid if t.faculty else "",
            "room": t.classroom.room_number if t.classroom else ""
        })

    # Calculate actual attendance for this faculty's classes
    attendance_data = {}
    from models import Attendance
    # Find all courses taught by any faculty, or we can just aggregate all attendance
    # and let the frontend filter, or pre-calculate class-wise averages.
    all_attendance = Attendance.query.all()
    for att in all_attendance:
        course_obj = Course.query.get(att.course_id)
        course_code = course_obj.code if course_obj else 'UNKNOWN'
        key = f"{course_code}_{att.section_id}"
        if key not in attendance_data:
            attendance_data[key] = {'total': 0, 'present': 0}
        attendance_data[key]['total'] += 1
        if att.status == 'present':
            attendance_data[key]['present'] += 1
            
    for key in attendance_data:
        tot = attendance_data[key]['total']
        pres = attendance_data[key]['present']
        attendance_data[key]['pct'] = round((pres / tot * 100), 1) if tot > 0 else 0

    DATA = {
        "faculty": faculty_list,
        "sections": sections_list,
        "students": students_list,
        "courses": courses_list,
        "timetable": timetable_list,
        "attendance": attendance_data,
        "facultyAbsence": {}
    }

    current_email = request.args.get('email', session.get('user_email', ''))

    return render_template('faculty_dashboard.html', DATA=json.dumps(DATA), current_email=current_email)


@faculty_bp.route('/timetable/faculty')
@login_required
@role_required('faculty')
def timetable_faculty_page():
    return render_template('timetable_faculty.html')
