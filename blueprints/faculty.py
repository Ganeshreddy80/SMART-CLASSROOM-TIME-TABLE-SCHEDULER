"""
Faculty blueprint — faculty dashboard, timetable, attendance APIs and pages.
"""
from flask import Blueprint, render_template, request, session, jsonify
import json

from models import (Faculty, Student, Section, Course, TimetableEntry, Attendance, db)
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
            "password": "password",
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

    attendance_data = {}
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


@faculty_bp.route('/faculty/api/attendance', methods=['GET'])
@login_required
@role_required('faculty', 'admin')
def faculty_attendance_api():
    """Return attendance records for courses taught by this faculty.
    Grouped by course, section, and date.
    Optional query params: course_id, section_id, date
    """
    faculty_id = session.get('user_id')

    # Get all timetable entries for this faculty
    entries = TimetableEntry.query.filter_by(faculty_id=faculty_id).all()
    course_ids = list({e.course_id for e in entries})
    section_ids = list({e.section_id for e in entries})

    if not course_ids:
        return jsonify({'records': [], 'summary': {}})

    # Optional filters
    filter_course = request.args.get('course_id', type=int)
    filter_section = request.args.get('section_id', type=int)
    filter_date = request.args.get('date')

    query = Attendance.query.filter(
        Attendance.course_id.in_(course_ids),
        Attendance.section_id.in_(section_ids)
    )

    if filter_course:
        query = query.filter_by(course_id=filter_course)
    if filter_section:
        query = query.filter_by(section_id=filter_section)
    if filter_date:
        try:
            from datetime import datetime
            dt = datetime.strptime(filter_date, '%Y-%m-%d').date()
            query = query.filter_by(date=dt)
        except Exception:
            pass

    records = query.order_by(Attendance.date.desc()).all()

    # Build grouped structure: { course_code: { section_id: { date: { present, absent, students[] } } } }
    grouped = {}
    summary = {}

    for r in records:
        course = Course.query.get(r.course_id)
        student = Student.query.get(r.student_id)
        section = Section.query.get(r.section_id)

        course_code = course.code if course else str(r.course_id)
        date_str = r.date.isoformat()
        sec_id = str(r.section_id)
        sec_name = section.name if section else str(r.section_id)

        if course_code not in grouped:
            grouped[course_code] = {
                'course_id': r.course_id,
                'course_name': course.name if course else '',
                'sections': {}
            }

        if sec_id not in grouped[course_code]['sections']:
            grouped[course_code]['sections'][sec_id] = {
                'section_name': sec_name,
                'dates': {}
            }

        if date_str not in grouped[course_code]['sections'][sec_id]['dates']:
            grouped[course_code]['sections'][sec_id]['dates'][date_str] = {
                'present': 0,
                'absent': 0,
                'od': 0,
                'students': []
            }

        day_data = grouped[course_code]['sections'][sec_id]['dates'][date_str]
        if r.status == 'present':
            day_data['present'] += 1
        elif r.status == 'absent':
            day_data['absent'] += 1
        else:
            day_data['od'] += 1

        day_data['students'].append({
            'student_id': r.student_id,
            'student_name': student.name if student else '',
            'reg_no': student.student_uid if student else '',
            'status': r.status
        })

        # Summary per course
        key = course_code
        if key not in summary:
            summary[key] = {'total': 0, 'present': 0}
        summary[key]['total'] += 1
        if r.status == 'present':
            summary[key]['present'] += 1

    for key in summary:
        tot = summary[key]['total']
        pres = summary[key]['present']
        summary[key]['pct'] = round((pres / tot * 100), 1) if tot > 0 else 0

    return jsonify({'grouped': grouped, 'summary': summary})


@faculty_bp.route('/api/faculty-absences')
@login_required
def faculty_absences():
    from models import Timetable, Attendance, Faculty
    from sqlalchemy import func
    import datetime

    today = datetime.date.today()
    thirty_days_ago = today - datetime.timedelta(days=30)

    results = db.session.execute(db.text("""
        SELECT 
            t.faculty_id,
            t.day_of_week,
            COUNT(t.id) as slots
        FROM timetable t
        WHERE t.faculty_id IS NOT NULL
        GROUP BY t.faculty_id, t.day_of_week
    """)).fetchall()

    data = []
    for row in results:
        data.append({
            'faculty_id': row[0],
            'day': row[1],
            'slots': row[2]
        })

    return jsonify(data)


@faculty_bp.route('/faculty/attendance-management')
@login_required
@role_required('faculty', 'admin')
def faculty_attendance_management():
    """Attendance management page — select course/section/date, toggle present/absent, save."""
    return render_template('attendance_management.html')
