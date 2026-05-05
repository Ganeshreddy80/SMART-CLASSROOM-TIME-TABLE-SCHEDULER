"""
API blueprint — all /api/* JSON routes.
Registered with url_prefix='/api', so route decorators omit the /api prefix.
"""
from flask import Blueprint, request, jsonify, session
import json, math, os
from datetime import date as date_type

import requests as http_requests

from models import (db, University, Department, Course, Faculty, Student, Section,
                    Classroom, TimetableEntry, Attendance, FacultyAbsence,
                    faculty_courses, student_courses, section_students,
                    generate_email_from_name, generate_default_password, ensure_unique_email)
from timetable_generator import generate_timetable
from blueprints.utils import login_required, role_required, calc_classes_per_week

api = Blueprint('api', __name__, url_prefix='/api')


# ─── Dashboard ───────────────────────────────────────────────
@api.route('/dashboard')
@login_required
@role_required('admin')
def api_dashboard():
    # Calculate theoretical timetable entries: 
    # sum of (classes_per_week for all courses in a department) * (number of sections in that department)
    total_entries = 0
    depts = Department.query.all()
    for d in depts:
        sections_in_dept = Section.query.filter_by(department_id=d.id).count()
        courses_in_dept = Course.query.filter_by(department_id=d.id).all()
        classes_sum = sum(c.classes_per_week for c in courses_in_dept)
        total_entries += (sections_in_dept * classes_sum)

    return jsonify({
        'departments': Department.query.count(),
        'students': Student.query.count(),
        'faculty': Faculty.query.count(),
        'courses': Course.query.count(),
        'sections': Section.query.count(),
        'timetable_entries': total_entries
    })


# ─── University ──────────────────────────────────────────────
@api.route('/university', methods=['GET'])
@login_required
@role_required('admin')
def get_university():
    u = University.query.first()
    if u:
        return jsonify(u.to_dict())
    return jsonify({})


@api.route('/university', methods=['POST'])
@login_required
@role_required('admin')
def save_university():
    data = request.json
    u = University.query.first()
    if not u:
        u = University()
        db.session.add(u)
    u.name = data.get('name', 'My University')
    u.total_blocks = int(data.get('total_blocks', 2))
    u.floors_per_block = json.dumps(data.get('floors_per_block', {}))
    u.rooms_per_block = int(data.get('rooms_per_block', 5))
    u.room_capacity = int(data.get('room_capacity', 60))
    u.days = json.dumps(data.get('days', ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']))
    u.timeslots = json.dumps(data.get('timeslots', []))
    db.session.commit()

    # University structure changes invalidate existing timetable allocations.
    TimetableEntry.query.delete()

    # Auto-generate classrooms (per block → per floor → per room)
    floors_map = u.get_floors_per_block()
    Classroom.query.delete()
    for block in range(1, u.total_blocks + 1):
        num_floors = int(floors_map.get(str(block), 3))
        for floor in range(1, num_floors + 1):
            for room in range(1, u.rooms_per_block + 1):
                c = Classroom(
                    block=block,
                    floor=floor,
                    room_number=f"B{block}-F{floor}-R{room}",
                    capacity=u.room_capacity,
                    room_type='Theory'
                )
                db.session.add(c)
    db.session.commit()
    return jsonify({'message': 'University settings saved', 'data': u.to_dict()})


# ─── Department CRUD ─────────────────────────────────────────
@api.route('/departments', methods=['GET'])
@login_required
@role_required('admin')
def get_departments():
    depts = Department.query.all()
    return jsonify([d.to_dict() for d in depts])


@api.route('/departments', methods=['POST'])
@login_required
@role_required('admin')
def create_department():
    data = request.json
    d = Department(name=data['name'], code=data['code'])
    db.session.add(d)
    db.session.commit()
    return jsonify(d.to_dict()), 201


@api.route('/departments/<int:id>', methods=['PUT'])
@login_required
@role_required('admin')
def update_department(id):
    data = request.json
    d = Department.query.get_or_404(id)
    d.name = data.get('name', d.name)
    d.code = data.get('code', d.code)
    db.session.commit()
    return jsonify(d.to_dict())


@api.route('/departments/<int:id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_department(id):
    d = Department.query.get_or_404(id)
    db.session.delete(d)
    db.session.commit()
    return jsonify({'message': 'Deleted'})


# ─── Course CRUD ─────────────────────────────────────────────
@api.route('/courses', methods=['GET'])
@login_required
@role_required('admin')
def get_courses():
    courses = Course.query.all()
    return jsonify([c.to_dict() for c in courses])


@api.route('/courses', methods=['POST'])
@login_required
@role_required('admin')
def create_course():
    data = request.json
    credits = int(data.get('credits', 3))
    difficulty = data.get('difficulty', 'Medium')
    cpw = calc_classes_per_week(difficulty, credits)
    c = Course(
        code=data['code'], name=data['name'],
        department_id=int(data['department_id']),
        credits=credits, difficulty=difficulty,
        classes_per_week=cpw,
        course_type=data.get('course_type', 'Theory')
    )
    db.session.add(c)
    db.session.commit()
    return jsonify(c.to_dict()), 201


@api.route('/courses/<int:id>', methods=['PUT'])
@login_required
@role_required('admin')
def update_course(id):
    data = request.json
    c = Course.query.get_or_404(id)
    c.code = data.get('code', c.code)
    c.name = data.get('name', c.name)
    c.department_id = int(data.get('department_id', c.department_id))
    c.credits = int(data.get('credits', c.credits))
    c.difficulty = data.get('difficulty', c.difficulty)
    c.course_type = data.get('course_type', c.course_type)
    c.classes_per_week = calc_classes_per_week(c.difficulty, c.credits)
    db.session.commit()
    return jsonify(c.to_dict())


@api.route('/courses/<int:id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_course(id):
    c = Course.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({'message': 'Deleted'})


# ─── Faculty CRUD ────────────────────────────────────────────
@api.route('/faculty', methods=['GET'])
@login_required
def get_faculty():
    facs = Faculty.query.all()
    return jsonify([f.to_dict() for f in facs])


@api.route('/faculty', methods=['POST'])
@login_required
@role_required('admin')
def create_faculty():
    data = request.json
    name = data['name']

    # Auto-generate email and password
    raw_email = generate_email_from_name(name)
    email = ensure_unique_email(raw_email)
    default_pw = generate_default_password(name)

    f = Faculty(
        faculty_uid=data['faculty_uid'],
        name=name,
        email=email,
        department_id=int(data['department_id']),
        available_slots=json.dumps(data.get('available_slots', {}))
    )
    f.set_password(default_pw)

    # Assign courses
    course_ids = data.get('courses_can_teach', [])
    if course_ids:
        courses = Course.query.filter(Course.id.in_(course_ids)).all()
        f.courses_can_teach = courses
    db.session.add(f)
    db.session.commit()
    result = f.to_dict()
    result['default_password'] = default_pw
    return jsonify(result), 201


@api.route('/faculty/<int:id>', methods=['PUT'])
@login_required
@role_required('admin')
def update_faculty(id):
    data = request.json
    f = Faculty.query.get_or_404(id)
    old_name = f.name
    f.faculty_uid = data.get('faculty_uid', f.faculty_uid)
    f.name = data.get('name', f.name)
    f.department_id = int(data.get('department_id', f.department_id))
    f.available_slots = json.dumps(data.get('available_slots', f.get_available_slots()))

    # If name changed, regenerate email
    if f.name != old_name:
        raw_email = generate_email_from_name(f.name)
        f.email = ensure_unique_email(raw_email, exclude_faculty_id=f.id)

    course_ids = data.get('courses_can_teach', [])
    if course_ids is not None:
        courses = Course.query.filter(Course.id.in_(course_ids)).all()
        f.courses_can_teach = courses
    db.session.commit()
    return jsonify(f.to_dict())


@api.route('/faculty/<int:id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_faculty(id):
    f = Faculty.query.get_or_404(id)
    db.session.delete(f)
    db.session.commit()
    return jsonify({'message': 'Deleted'})


@api.route('/faculty/<int:id>/photo', methods=['POST'])
@login_required
@role_required('admin')
def upload_faculty_photo(id):
    f = Faculty.query.get_or_404(id)
    data = request.json or {}
    photo_data = data.get('photo')
    if not photo_data:
        return jsonify({'error': 'No photo provided'}), 400
    if not photo_data.startswith('data:image'):
        return jsonify({'error': 'Invalid image format'}), 400
    f.photo_url = photo_data
    db.session.commit()
    return jsonify({'message': 'Photo saved', 'photo_url': f.photo_url})


# ─── Student CRUD ────────────────────────────────────────────
@api.route('/students', methods=['GET'])
@login_required
def get_students():
    section_id = request.args.get('section_id')
    if section_id:
        students = Student.query.filter(Student.sections.any(id=section_id)).all()
    else:
        students = Student.query.all()
    return jsonify([s.to_dict() for s in students])


@api.route('/students', methods=['POST'])
@login_required
@role_required('admin')
def create_student():
    data = request.json
    name = data['name']

    # Auto-generate email and password
    raw_email = generate_email_from_name(name)
    email = ensure_unique_email(raw_email)
    default_pw = generate_default_password(name)

    s = Student(
        student_uid=data['student_uid'],
        name=name,
        email=email,
        department_id=int(data['department_id'])
    )
    s.set_password(default_pw)

    course_ids = data.get('courses_enrolled', [])
    if course_ids:
        courses = Course.query.filter(Course.id.in_(course_ids)).all()
        s.courses_enrolled = courses
    db.session.add(s)
    db.session.commit()
    result = s.to_dict()
    result['default_password'] = default_pw
    return jsonify(result), 201


@api.route('/students/<int:id>', methods=['PUT'])
@login_required
@role_required('admin')
def update_student(id):
    data = request.json
    s = Student.query.get_or_404(id)
    old_name = s.name
    s.student_uid = data.get('student_uid', s.student_uid)
    s.name = data.get('name', s.name)
    s.department_id = int(data.get('department_id', s.department_id))

    # If name changed, regenerate email
    if s.name != old_name:
        raw_email = generate_email_from_name(s.name)
        s.email = ensure_unique_email(raw_email, exclude_student_id=s.id)

    course_ids = data.get('courses_enrolled', [])
    if course_ids is not None:
        courses = Course.query.filter(Course.id.in_(course_ids)).all()
        s.courses_enrolled = courses
    db.session.commit()
    return jsonify(s.to_dict())


@api.route('/students/<int:id>/photo', methods=['POST'])
@login_required
@role_required('admin')
def upload_student_photo(id):
    s = Student.query.get_or_404(id)
    data = request.json
    photo_data = data.get('photo')
    if not photo_data:
        return jsonify({'error': 'No photo provided'}), 400
    # Ensure it has proper base64 header
    if not photo_data.startswith('data:image'):
        return jsonify({'error': 'Invalid image format'}), 400
    s.photo_url = photo_data
    db.session.commit()
    return jsonify({'message': 'Photo saved', 'photo_url': s.photo_url})


@api.route('/students/<int:id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_student(id):
    s = Student.query.get_or_404(id)
    db.session.delete(s)
    db.session.commit()
    return jsonify({'message': 'Deleted'})


# ─── Section Generation ─────────────────────────────────────
@api.route('/sections/generate', methods=['POST'])
@login_required
@role_required('admin')
def generate_sections():
    # Regenerating sections invalidates old timetable and section mappings.
    TimetableEntry.query.delete()
    db.session.execute(section_students.delete())

    # Clear existing sections
    Section.query.delete()
    db.session.commit()

    departments = Department.query.all()
    sections_created = []

    for dept in departments:
        students = Student.query.filter_by(department_id=dept.id).all()
        total = len(students)
        if total == 0:
            continue

        num_sections = math.ceil(total / 60)
        per_section = math.ceil(total / num_sections)

        for i in range(num_sections):
            section_name = chr(65 + i)  # A, B, C...
            start = i * per_section
            end = min(start + per_section, total)
            section_students_list = students[start:end]

            sec = Section(
                name=section_name,
                department_id=dept.id,
                student_count=len(section_students_list)
            )
            sec.students = section_students_list
            db.session.add(sec)
            sections_created.append({
                'department': dept.code,
                'section': section_name,
                'count': len(section_students_list)
            })

    db.session.commit()
    return jsonify({'message': f'{len(sections_created)} sections created', 'sections': sections_created})


@api.route('/sections', methods=['GET'])
@login_required
def get_sections():
    # Students can only see their own section(s)
    if session.get('role') == 'student':
        student = Student.query.get(session['user_id'])
        if student:
            return jsonify([s.to_dict() for s in student.sections])
        return jsonify([])
    sections = Section.query.all()
    return jsonify([s.to_dict() for s in sections])


# ─── Classroom API ───────────────────────────────────────────
@api.route('/classrooms', methods=['GET'])
@login_required
@role_required('admin')
def get_classrooms():
    rooms = Classroom.query.all()
    return jsonify([r.to_dict() for r in rooms])


# ─── Timetable Generation ───────────────────────────────────
@api.route('/timetable/generate', methods=['POST'])
@login_required
@role_required('admin')
def api_generate_timetable():
    result = generate_timetable()
    return jsonify(result)


@api.route('/timetable/section/<int:section_id>', methods=['GET'])
@login_required
def get_section_timetable(section_id):
    # If student, enforce they can only see their own section
    if session.get('role') == 'student':
        allowed_ids = session.get('section_ids', [])
        if section_id not in allowed_ids:
            return jsonify({'error': 'Access denied. You can only view your own section.'}), 403
    entries = TimetableEntry.query.filter_by(section_id=section_id).all()
    return jsonify([e.to_dict() for e in entries])


@api.route('/timetable/faculty/<int:faculty_id>', methods=['GET'])
@login_required
@role_required('faculty')
def get_faculty_timetable(faculty_id):
    entries = TimetableEntry.query.filter_by(faculty_id=faculty_id).all()
    return jsonify([e.to_dict() for e in entries])


@api.route('/timetable/student/<int:student_id>', methods=['GET'])
@login_required
def get_student_timetable(student_id):
    # Security: enforce that student can only access their own timetable
    if session.get('role') == 'student' and session.get('user_id') != student_id:
        return jsonify({'error': 'Access denied'}), 403

    student = Student.query.get_or_404(student_id)
    section_ids = [s.id for s in student.sections]
    course_ids = [c.id for c in student.courses_enrolled]

    if not section_ids or not course_ids:
        return jsonify([])

    query = TimetableEntry.query.filter(
        TimetableEntry.section_id.in_(section_ids),
        TimetableEntry.course_id.in_(course_ids)
    )

    # Optional day filter for "today's timetable" view
    day_filter = request.args.get('day')
    if day_filter:
        query = query.filter(TimetableEntry.day == day_filter)

    entries = query.all()
    return jsonify([e.to_dict() for e in entries])


# ─── Attendance APIs ────────────────────────────────────────
@api.route('/attendance/student/<int:student_id>', methods=['GET'])
@login_required
def get_student_attendance(student_id):
    """Get subject-wise and overall attendance for a student."""
    # Security: student can only view their own attendance
    if session.get('role') == 'student' and session.get('user_id') != student_id:
        return jsonify({'error': 'Access denied'}), 403

    student = Student.query.get_or_404(student_id)
    records = Attendance.query.filter_by(student_id=student_id).all()

    # Build subject-wise summary and trend
    from datetime import timedelta
    today = date_type.today()
    weeks_data = {0: {'total': 0, 'present': 0}, 1: {'total': 0, 'present': 0}, 2: {'total': 0, 'present': 0}, 3: {'total': 0, 'present': 0}}
    
    course_stats = {}  # course_id -> {total, present, course_name, course_code}
    for rec in records:
        cid = rec.course_id
        if cid not in course_stats:
            course = Course.query.get(cid)
            course_stats[cid] = {
                'course_id': cid,
                'course_name': course.name if course else '',
                'course_code': course.code if course else '',
                'total': 0,
                'present': 0
            }
        course_stats[cid]['total'] += 1
        if rec.status == 'present':
            course_stats[cid]['present'] += 1
            
        # Calculate week offset (0 = this week, 3 = 3 weeks ago)
        days_ago = (today - rec.date).days
        week_idx = days_ago // 7
        if 0 <= week_idx <= 3:
            weeks_data[week_idx]['total'] += 1
            if rec.status == 'present':
                weeks_data[week_idx]['present'] += 1

    # Calculate percentages
    subjects = []
    total_classes = 0
    total_present = 0
    for cid, stats in course_stats.items():
        pct = round((stats['present'] / stats['total'] * 100), 1) if stats['total'] > 0 else 0
        subjects.append({
            'course_id': stats['course_id'],
            'course_name': stats['course_name'],
            'course_code': stats['course_code'],
            'total_classes': stats['total'],
            'classes_attended': stats['present'],
            'percentage': pct
        })
        total_classes += stats['total']
        total_present += stats['present']

    overall_pct = round((total_present / total_classes * 100), 1) if total_classes > 0 else 0
    
    trend = []
    for i in range(3, -1, -1):
        w_tot = weeks_data[i]['total']
        w_pres = weeks_data[i]['present']
        pct = round((w_pres / w_tot * 100), 1) if w_tot > 0 else (overall_pct if overall_pct > 0 else 0)
        trend.append({
            'label': f"{i} weeks ago" if i > 0 else "This week",
            'percentage': pct
        })

    return jsonify({
        'student_id': student_id,
        'student_name': student.name,
        'overall_percentage': overall_pct,
        'total_classes': total_classes,
        'total_present': total_present,
        'subjects': subjects,
        'trend': trend
    })

@api.route('/attendance/low', methods=['GET'])
@login_required
@role_required('admin')
def get_low_attendance():
    """Return list of students with overall attendance < 75%"""
    students = Student.query.all()
    records = Attendance.query.all()
    
    # Pre-aggregate attendance
    att_map = {}
    for r in records:
        if r.student_id not in att_map:
            att_map[r.student_id] = {'total': 0, 'present': 0}
        att_map[r.student_id]['total'] += 1
        if r.status == 'present':
            att_map[r.student_id]['present'] += 1
            
    low_students = []
    for s in students:
        stats = att_map.get(s.id)
        if stats and stats['total'] > 0:
            pct = round((stats['present'] / stats['total'] * 100), 1)
            if pct < 75:
                low_students.append({
                    'id': s.id,
                    'uid': s.student_uid,
                    'name': s.name,
                    'department': s.department.code if s.department else '',
                    'percentage': pct
                })
                
    # Sort by lowest percentage first
    low_students.sort(key=lambda x: x['percentage'])
    
    return jsonify(low_students)



@api.route('/attendance/mark', methods=['POST'])
@login_required
@role_required('faculty', 'admin')
def mark_attendance():
    """Mark attendance for a section+course+date. Faculty/Admin only."""
    data = request.json
    section_id = data.get('section_id')
    course_id = data.get('course_id')
    date_str = data.get('date')  # YYYY-MM-DD
    present_student_ids = data.get('present_student_ids', [])

    if not all([section_id, course_id, date_str]):
        return jsonify({'error': 'section_id, course_id, and date are required'}), 400

    try:
        att_date = date_type.fromisoformat(date_str)
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    # Get all students in the section
    section = Section.query.get_or_404(section_id)
    all_student_ids = [s.id for s in section.students]

    # Delete existing attendance for this section+course+date (re-mark)
    Attendance.query.filter_by(
        section_id=section_id, course_id=course_id, date=att_date
    ).delete()

    # Create attendance records
    for sid in all_student_ids:
        status = 'present' if sid in present_student_ids else 'absent'
        att = Attendance(
            student_id=sid,
            course_id=course_id,
            section_id=section_id,
            date=att_date,
            status=status
        )
        db.session.add(att)

    db.session.commit()
    return jsonify({
        'message': f'Attendance marked for {len(all_student_ids)} students',
        'present': len(present_student_ids),
        'absent': len(all_student_ids) - len(present_student_ids)
    })


@api.route('/timetable/rooms', methods=['GET'])
@login_required
@role_required('admin')
def get_room_timetable():
    block = request.args.get('block')
    query = TimetableEntry.query
    if block:
        room_ids = [r.id for r in Classroom.query.filter_by(block=int(block)).all()]
        query = query.filter(TimetableEntry.classroom_id.in_(room_ids))
    entries = query.all()
    return jsonify([e.to_dict() for e in entries])


@api.route('/timetable/all', methods=['GET'])
@login_required
@role_required('admin')
def get_all_timetable():
    entries = TimetableEntry.query.all()
    return jsonify([e.to_dict() for e in entries])


@api.route('/room-utilization', methods=['GET'])
@login_required
@role_required('admin', 'faculty')
def get_room_utilization():
    university = University.query.first()
    days = university.get_days() if university else []
    timeslots = university.get_timeslots() if university else []
    classrooms = Classroom.query.all()
    
    entries = TimetableEntry.query.all()
    # Build utilization matrix
    # rows: room_id, cols: (day, timeslot)
    
    matrix = {}
    for r in classrooms:
        matrix[r.id] = {
            'room': r.to_dict(),
            'schedule': {},
            'used_slots': 0,
            'total_slots': len(days) * len(timeslots)
        }
        for d in days:
            matrix[r.id]['schedule'][d] = {ts: None for ts in timeslots}

    for e in entries:
        r_id = e.classroom_id
        if r_id in matrix:
            if e.day in matrix[r_id]['schedule'] and e.timeslot in matrix[r_id]['schedule'][e.day]:
                if matrix[r_id]['schedule'][e.day][e.timeslot] is None:
                    matrix[r_id]['used_slots'] += 1
                matrix[r_id]['schedule'][e.day][e.timeslot] = {
                    'course_code': e.course.code if e.course else '',
                    'section': f"{e.section.department.code}-{e.section.name}" if e.section else ''
                }

    for r_id in matrix:
        total = matrix[r_id]['total_slots']
        used = matrix[r_id]['used_slots']
        matrix[r_id]['utilization_pct'] = round((used / total * 100), 1) if total > 0 else 0

    return jsonify({
        'days': days,
        'timeslots': timeslots,
        'rooms': list(matrix.values())
    })



@api.route('/suggest-room', methods=['GET'])
@login_required
@role_required('admin')
def suggest_room():
    section_id = request.args.get('section_id', type=int)
    day = request.args.get('day')
    timeslot = request.args.get('timeslot')
    
    if not all([section_id, day, timeslot]):
        return jsonify({'error': 'Missing parameters'}), 400
        
    section = Section.query.get_or_404(section_id)
    student_count = section.student_count
    
    # Find previous class for the section on this day
    university = University.query.first()
    timeslots = university.get_timeslots() if university else []
    
    prev_block = None
    try:
        ts_idx = timeslots.index(timeslot)
        if ts_idx > 0:
            prev_ts = timeslots[ts_idx - 1]
            prev_entry = TimetableEntry.query.filter_by(section_id=section_id, day=day, timeslot=prev_ts).first()
            if prev_entry and prev_entry.classroom:
                prev_block = prev_entry.classroom.block
    except ValueError:
        pass
        
    # Find all occupied rooms at this timeslot
    occupied = TimetableEntry.query.filter_by(day=day, timeslot=timeslot).all()
    occupied_ids = [e.classroom_id for e in occupied]
    
    # Filter classrooms: free and capacity >= student_count
    available = Classroom.query.filter(
        ~Classroom.id.in_(occupied_ids),
        Classroom.capacity >= student_count
    ).all()
    
    # Sort rooms:
    # 1. Same block as previous class (if any) -> True comes before False
    # 2. Capacity difference (closest fit first)
    
    def room_score(r):
        is_same_block = 0 if (prev_block and r.block == prev_block) else 1
        cap_diff = r.capacity - student_count
        return (is_same_block, cap_diff)
        
    available.sort(key=room_score)
    
    return jsonify([
        {
            **r.to_dict(), 
            'suggestion_reason': 'Same block' if (prev_block and r.block == prev_block) else 'Closest capacity'
        } for r in available[:5]  # return top 5 suggestions
    ])

@api.route('/timetable/entry/<int:id>', methods=['PUT'])
@login_required
@role_required('admin')
def update_timetable_entry(id):
    entry = TimetableEntry.query.get_or_404(id)
    data = request.json
    
    if 'classroom_id' in data:
        new_room_id = data['classroom_id']
        # Verify it's free
        conflict = TimetableEntry.query.filter_by(day=entry.day, timeslot=entry.timeslot, classroom_id=new_room_id).first()
        if conflict and conflict.id != entry.id:
            return jsonify({'error': 'Room is already occupied at this time'}), 400
        entry.classroom_id = new_room_id
        
    db.session.commit()
    return jsonify(entry.to_dict())

# ─── AI Chatbot (OpenRouter) ────────────────────────────────
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENROUTER_MODEL = 'openai/gpt-4o-mini'
OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'


def _get_system_context():
    """Gather all database data as context for the AI."""
    uni = University.query.first()
    depts = Department.query.all()
    courses = Course.query.all()
    faculty = Faculty.query.all()
    students = Student.query.all()
    sections = Section.query.all()
    entries = TimetableEntry.query.all()
    classrooms = Classroom.query.all()

    ctx = f"""You are UniSchedule AI — an intelligent assistant for a University Timetable Management System.
You help administrators with data queries, scheduling insights, and smart suggestions.
Answer concisely and use tables/lists when showing data. Be friendly and professional.

=== UNIVERSITY DATA ===
University: {uni.name if uni else 'Not configured'}
Blocks: {uni.total_blocks if uni else 0}, Rooms per floor: {uni.rooms_per_block if uni else 0}
Days: {uni.get_days() if uni else []}
Timeslots: {uni.get_timeslots() if uni else []}
Total Classrooms: {len(classrooms)}

=== DEPARTMENTS ({len(depts)}) ===
"""
    for d in depts:
        dept_students = [s for s in students if s.department_id == d.id]
        dept_courses = [c for c in courses if c.department_id == d.id]
        dept_faculty = [f for f in faculty if f.department_id == d.id]
        ctx += f"• {d.code} - {d.name}: {len(dept_students)} students, {len(dept_courses)} courses, {len(dept_faculty)} faculty\n"

    ctx += f"\n=== COURSES ({len(courses)}) ===\n"
    for c in courses:
        dept = next((d for d in depts if d.id == c.department_id), None)
        fac_list = [f.name for f in c.faculty_members]
        ctx += f"• {c.code} {c.name} ({dept.code if dept else '?'}) - {c.credits}cr, {c.difficulty}, {c.course_type}, {c.classes_per_week}cls/wk, Faculty: {', '.join(fac_list) or 'None'}\n"

    ctx += f"\n=== FACULTY ({len(faculty)}) ===\n"
    for f in faculty:
        dept = next((d for d in depts if d.id == f.department_id), None)
        teaching = [c.code for c in f.courses_can_teach]
        fac_entries = [e for e in entries if e.faculty_id == f.id]
        ctx += f"• {f.faculty_uid} {f.name} ({dept.code if dept else '?'}) - teaches: {', '.join(teaching)}, {len(fac_entries)} classes/week\n"

    ctx += f"\n=== SECTIONS ({len(sections)}) ===\n"
    for s in sections:
        dept = next((d for d in depts if d.id == s.department_id), None)
        sec_entries = [e for e in entries if e.section_id == s.id]
        ctx += f"• {dept.code if dept else '?'}-{s.name}: {s.student_count} students, {len(sec_entries)} timetable slots\n"

    ctx += f"\n=== TIMETABLE SUMMARY ===\n"
    ctx += f"Total entries: {len(entries)}\n"

    # Room utilization
    total_slots = len(uni.get_days()) * len(uni.get_timeslots()) * len(classrooms) if uni else 0
    utilization = (len(entries) / total_slots * 100) if total_slots > 0 else 0
    ctx += f"Room utilization: {utilization:.1f}% ({len(entries)}/{total_slots} slots used)\n"

    # Faculty workload summary
    fac_loads = {}
    for e in entries:
        fac_loads[e.faculty_id] = fac_loads.get(e.faculty_id, 0) + 1
    if fac_loads:
        max_load = max(fac_loads.values())
        min_load = min(fac_loads.values())
        avg_load = sum(fac_loads.values()) / len(fac_loads)
        busiest = next((f.name for f in faculty if f.id == max(fac_loads, key=fac_loads.get)), '?')
        ctx += f"Faculty workload: min={min_load}, max={max_load}, avg={avg_load:.1f}\n"
        ctx += f"Busiest faculty: {busiest} ({max_load} classes/week)\n"

    return ctx


@api.route('/attendance/trend/<int:student_id>', methods=['GET'])
@login_required
def get_attendance_trend(student_id):
    """Returns attendance percentage over the last 4 weeks."""
    if session.get('role') != 'admin' and session.get('user_id') != student_id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    import datetime
    from models import Attendance
    today = datetime.date.today()
    weeks = []
    for i in range(4):
        start = today - datetime.timedelta(days=(i+1)*7)
        end = today - datetime.timedelta(days=i*7)
        
        total = Attendance.query.filter(
            Attendance.student_id == student_id,
            Attendance.date >= start,
            Attendance.date < end
        ).count()
        
        present = Attendance.query.filter(
            Attendance.student_id == student_id,
            Attendance.date >= start,
            Attendance.date < end,
            Attendance.status == 'present'
        ).count()
        
        pct = round((present / total * 100), 1) if total > 0 else 100 # Default to 100 if no classes
        weeks.append({'week': f'Week {4-i}', 'pct': pct})
        
    return jsonify(weeks[::-1])

@api.route('/attendance/stats', methods=['GET'])
@login_required
def get_attendance_stats():
    """Returns overall attendance stats for the user (student/faculty)."""
    uid = session.get('user_id')
    role = session.get('role')
    
    from models import Attendance
    if role == 'student':
        records = Attendance.query.filter_by(student_id=uid).all()
        # group by course
        stats = {}
        for r in records:
            c_code = r.course.code if r.course else 'Unknown'
            if c_code not in stats: stats[c_code] = {'total':0, 'present':0}
            stats[c_code]['total'] += 1
            if r.status == 'present': stats[c_code]['present'] += 1
        
        res = []
        for code, s in stats.items():
            res.append({'course': code, 'pct': round(s['present']/s['total']*100, 1)})
        return jsonify(res)
        
    return jsonify([])

@api.route('/chat', methods=['POST'])
@login_required
def chat():
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == 'paste-your-openrouter-api-key-here':
        return jsonify({'reply': 'OpenRouter API key not configured. Add OPENROUTER_API_KEY to your .env file.'}), 400

    data = request.json
    user_msg = data.get('message', '').strip()
    history = data.get('history', [])

    if not user_msg:
        return jsonify({'reply': 'Please type a message.'}), 400

    try:
        context = _get_system_context()

        # Build messages array in OpenAI chat format
        messages = [
            {'role': 'system', 'content': context}
        ]

        # Append conversation history (last 10 exchanges)
        for h in history[-10:]:
            messages.append({'role': 'user', 'content': h['user']})
            messages.append({'role': 'assistant', 'content': h['bot']})

        # Append the current user message
        messages.append({
            'role': 'user',
            'content': f"{user_msg}\n\nRespond helpfully. If asked about data, use the system context. Format responses with markdown for readability. Keep responses concise but informative."
        })

        # Call OpenRouter API
        response = http_requests.post(
            OPENROUTER_URL,
            headers={
                'Authorization': f'Bearer {OPENROUTER_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': OPENROUTER_MODEL,
                'messages': messages
            },
            timeout=30
        )

        if response.status_code != 200:
            error_detail = response.json().get('error', {}).get('message', response.text)
            return jsonify({'reply': f'API Error ({response.status_code}): {error_detail}'}), 500

        result = response.json()
        reply = result.get('choices', [{}])[0].get('message', {}).get('content', 'Sorry, no response received.')
        return jsonify({'reply': reply})

    except http_requests.exceptions.Timeout:
        return jsonify({'reply': 'The AI took too long to respond. Please try again.'}), 504
    except http_requests.exceptions.ConnectionError:
        return jsonify({'reply': 'Could not connect to the AI service. Check your network.'}), 503
    except Exception as e:
        return jsonify({'reply': f'Sorry, I encountered an error: {str(e)}'}), 500


# ─── Faculty Absence API ──────────────────────────────────────
@api.route('/faculty/absences', methods=['GET'])
@login_required
def get_faculty_absences():
    """Retrieve all recorded faculty absences."""
    absences = FacultyAbsence.query.all()
    return jsonify([a.to_dict() for a in absences])

@api.route('/admin/add-student', methods=['POST'])
@login_required
@role_required('admin')
def add_new_student():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    dept_id = data.get('department_id')
    
    if not all([name, email, dept_id]):
        return jsonify({"error": "Missing fields"}), 400

    # 1. Find sections for this dept
    sections = Section.query.filter_by(department_id=dept_id).all()
    if not sections:
        return jsonify({"error": "No sections found for this department"}), 400
        
    # 2. Find section with smallest strength
    target_section = min(sections, key=lambda s: s.student_count)
    
    # 3. Create Student
    student_count = Student.query.count()
    new_uid = f"STU{str(student_count + 1).zfill(4)}"
    
    new_student = Student(
        student_uid=new_uid,
        name=name,
        email=email,
        department_id=dept_id
    )
    
    from models import generate_default_password
    pwd = generate_default_password(name)
    new_student.set_password(pwd)
    
    db.session.add(new_student)
    
    # 4. Link to Section
    target_section.students.append(new_student)
    target_section.student_count += 1
    
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": f"Student {name} successfully enrolled in {target_section.department.name} - Section {target_section.name}",
        "credentials": {"email": email, "password": pwd},
        "student_uid": new_uid,
        "section_id": target_section.id,
        "section_name": target_section.name
    })

@api.route('/faculty/report-absence', methods=['POST'])
@login_required
@role_required('faculty', 'admin')
def report_faculty_absence():
    """Save or update faculty absence in database."""
    data = request.json
    fac_id = data.get('faculty_id') # This is the internal DB id
    date_str = data.get('date')
    slots = data.get('slots', [])
    reason = data.get('reason', '')

    if not all([fac_id, date_str]):
        return jsonify({'error': 'faculty_id and date are required'}), 400

    try:
        abs_date = date_type.fromisoformat(date_str)
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    # Handle internal vs UID
    faculty = Faculty.query.get(fac_id)
    if not faculty:
        faculty = Faculty.query.filter_by(faculty_uid=fac_id).first()
    
    if not faculty:
        return jsonify({'error': 'Faculty not found'}), 404

    # Remove existing record for this faculty+date if any
    FacultyAbsence.query.filter_by(faculty_id=faculty.id, date=abs_date).delete()

    if slots:
        new_abs = FacultyAbsence(
            faculty_id=faculty.id,
            date=abs_date,
            slots=json.dumps(slots),
            reason=reason
        )
        db.session.add(new_abs)

    db.session.commit()
    return jsonify({'message': 'Absence record updated', 'slots': slots})
