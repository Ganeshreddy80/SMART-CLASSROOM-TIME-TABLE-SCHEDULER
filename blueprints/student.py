"""
Student blueprint — student dashboard, timetable, attendance, marks pages + APIs.
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for

import json
from models import (db, Student, TimetableEntry, FacultyAbsence)
from blueprints.utils import login_required, role_required

student_bp = Blueprint('student_bp', __name__)


@student_bp.route('/student-app')
@login_required
@role_required('student', 'admin')
def student_app():
    return render_template('student_dashboard.html')


@student_bp.route('/timetable/student')
@login_required
@role_required('student')
def timetable_student_page():
    return render_template('timetable_student.html')


@student_bp.route('/attendance/student')
@login_required
@role_required('student')
def student_attendance_page():
    return render_template('student_attendance.html')


@student_bp.route('/student/logout')
def student_logout():
    session.clear()
    return redirect(url_for('auth.login_page'))


@student_bp.route('/student/upload-photo', methods=['POST'])
@login_required
def student_upload_photo():
    return jsonify({"message": "Photo uploaded successfully"})


@student_bp.route('/student/api/profile')
@login_required
def student_profile():
    if session.get('role') != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    s = Student.query.get(session.get('user_id'))
    if not s:
        return jsonify({'error': 'Student not found'}), 404

    return jsonify({
        'id': s.id,
        'name': s.name,
        'regNo': s.student_uid,
        'dept': s.department.name if s.department else '',
        'section': s.sections[0].id if s.sections else None,
        'sectionName': s.sections[0].name if s.sections else 'Unassigned',
        'year': 2,
        'semester': 4,
        'email': s.email,
        'phone': '+91 9876543210',
        'hostel': 'Hostel Block A',
        'advisor': 'Dr. Rajesh Kumar',
        'blood': 'O+',
        'dob': '2004-05-15',
        'cgpa': 8.75,
        'photo': s.photo_url or ''
    })


@student_bp.route('/student/api/courses')
@login_required
def student_courses_api():
    if session.get('role') != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    s = Student.query.get(session.get('user_id'))
    if not s:
        return jsonify([])
    res = []
    for c in s.courses_enrolled:
        res.append({
            'code': c.code,
            'name': c.name,
            'credits': c.credits,
            'type': c.course_type
        })
    return jsonify(res)


@student_bp.route('/student/api/timetable')
@login_required
def student_timetable():
    if session.get('role') != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    section_ids = session.get('section_ids', [])
    if not section_ids:
        return jsonify([])
    entries = TimetableEntry.query.filter(TimetableEntry.section_id.in_(section_ids)).all()
    res = []
    for e in entries:
        slot_str = e.timeslot
        parts = slot_str.split('-')
        if len(parts) == 2:
            s1 = parts[0].split(':')[0]
            s2 = parts[1].split(':')[0]
            slot_str = f"{s1}-{s2}"

        res.append({
            'day': e.day[:3],  # Mon, Tue...
            'slot': slot_str,
            'course': e.course.code if e.course else '',
            'faculty': e.faculty.name if e.faculty else '',
            'faculty_id': e.faculty.faculty_uid if e.faculty else '',
            'room': e.classroom.room_number if e.classroom else ''
        })
    return jsonify(res)


@student_bp.route('/student/api/attendance')
@login_required
def student_attendance_api():
    if session.get('role') != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    from models import Attendance
    s = Student.query.get(session.get('user_id'))
    if not s:
        return jsonify({})
    res = {}
    for c in s.courses_enrolled:
        records = Attendance.query.filter_by(student_id=s.id, course_id=c.id).all()
        total = len(records)
        present = sum(1 for r in records if r.status == 'present')
        absent = total - present
        pct = round((present / total) * 100, 1) if total > 0 else 0
        res[c.code] = {
            'total': total,
            'present': present,
            'absent': absent,
            'pct': pct
        }
    return jsonify(res)


@student_bp.route('/student/api/today-attendance')
@login_required
def student_today_attendance():
    return jsonify([])


@student_bp.route('/student/api/marks')
@login_required
def student_marks():
    return jsonify([
        {
            'sem': 1,
            'sgpa': 8.8,
            'subjects': [
                {'code': 'CS101', 'name': 'Data Structures', 'credits': 4, 'grade': 'A', 'points': 9},
                {'code': 'MA101', 'name': 'Calculus', 'credits': 4, 'grade': 'B+', 'points': 8}
            ]
        },
        {
            'sem': 2,
            'sgpa': 8.6,
            'subjects': [
                {'code': 'CS102', 'name': 'Algorithms', 'credits': 4, 'grade': 'A', 'points': 9},
                {'code': 'PH101', 'name': 'Physics', 'credits': 4, 'grade': 'A-', 'points': 8}
            ]
        }
    ])


@student_bp.route('/student/api/faculty-absence')
@login_required
def student_faculty_absence():
    absences = FacultyAbsence.query.all()
    res = {}
    for a in absences:
        f_id = a.faculty_id
        d_str = a.date.isoformat()
        if f_id not in res: res[f_id] = {}
        res[f_id][d_str] = json.loads(a.slots) if a.slots else []
    return jsonify(res)
