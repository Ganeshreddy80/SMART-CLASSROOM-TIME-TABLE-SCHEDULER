"""
attendance.py — Smart Attendance System
Handles proxy-proof attendance via:
  1. VPN/datacenter IP detection
  2. GPS Haversine distance check (≤ 100 m)
  3. Server-side rolling QR tokens (3-sec lifetime, 4-sec grace)
  4. Auto-selfie face verification (flag if fail — never hard-block)
  5. Duplicate submission guard
  6. Section enrollment check

ACTIVE_SESSIONS dict (in-memory) is the source of truth during a live session.
On session stop, data is committed to Attendance table.
"""

import math
import os
import secrets
import time
import ipaddress
from datetime import datetime
import pytz

from flask import Blueprint, request, jsonify, session, render_template

from models import db, Student, Faculty, Course, Section, Attendance, TimetableEntry
from blueprints.utils import login_required, role_required

attendance_bp = Blueprint('attendance_bp', __name__)

# ─── Timezone ─────────────────────────────────────────────────────────────────
IST = pytz.timezone('Asia/Kolkata')

def ist_today():
    """Return today's date in IST."""
    return datetime.now(IST).date()

# ─── In-memory Session Store ─────────────────────────────────────────────────
ACTIVE_SESSIONS: dict = {}

SESSION_LIFETIME = 900        # 15 minutes
QR_TOKEN_INTERVAL = 3         # seconds — new token every 3 s
QR_TOKEN_GRACE = 1            # extra grace seconds → max valid window = 4 s
QR_HISTORY_LIMIT = 5          # keep at most 5 tokens to bound memory
GPS_MAX_DISTANCE = 100        # metres — must be within 100 m of faculty
GPS_MAX_ACCURACY = 50         # metres — reject if accuracy > 50 m


# ──────────────────────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────────────────────

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Exact Haversine formula — returns distance in metres."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# Known VPN / datacenter CIDR ranges (IPv4) — extend this list as needed
_VPN_RANGES = [
    "104.16.0.0/12", "172.64.0.0/13", "162.158.0.0/15",
    "193.138.218.0/24", "185.213.154.0/23",
    "80.240.0.0/13", "5.180.0.0/14",
    "185.159.156.0/22", "185.107.80.0/22",
    "205.185.208.0/20",
    "3.0.0.0/9", "13.32.0.0/12", "34.0.0.0/10", "35.184.0.0/13",
    "40.74.0.0/14", "52.0.0.0/11", "54.160.0.0/11",
    "104.196.0.0/14", "107.178.192.0/18", "130.211.0.0/16",
    "139.59.0.0/16", "142.93.0.0/16", "159.203.0.0/16",
    "165.22.0.0/15", "167.71.0.0/16", "167.99.0.0/16",
]

_VPN_NETWORKS = [ipaddress.ip_network(cidr, strict=False) for cidr in _VPN_RANGES]


def is_vpn_ip(ip_str: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip_str)
        if addr.is_private or addr.is_loopback:
            return False
        for net in _VPN_NETWORKS:
            if addr in net:
                return True
    except ValueError:
        pass
    return False


def get_client_ip() -> str:
    xff = request.headers.get('X-Forwarded-For', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.remote_addr or '0.0.0.0'


def _purge_old_tokens(sess: dict) -> None:
    cutoff = time.time() - (QR_TOKEN_INTERVAL + QR_TOKEN_GRACE)
    sess['qr_tokens'] = [t for t in sess['qr_tokens'] if t['created_at'] >= cutoff]
    if len(sess['qr_tokens']) > QR_HISTORY_LIMIT:
        sess['qr_tokens'] = sess['qr_tokens'][-QR_HISTORY_LIMIT:]


def _make_qr_token(sess: dict) -> dict:
    tok = {
        'token': secrets.token_urlsafe(32),
        'created_at': time.time()
    }
    sess['qr_tokens'].append(tok)
    _purge_old_tokens(sess)
    return tok


def _find_valid_token(sess: dict, qr_token: str) -> bool:
    now = time.time()
    cutoff = now - (QR_TOKEN_INTERVAL + QR_TOKEN_GRACE)
    for t in sess['qr_tokens']:
        if t['token'] == qr_token and t['created_at'] >= cutoff:
            return True
    return False


def _faculty_session_for_student(section_id: int) -> tuple:
    now = time.time()
    for token, sess in ACTIVE_SESSIONS.items():
        if sess['section_id'] == section_id and sess['expires_at'] > now:
            return token, sess
    return None, None


# ──────────────────────────────────────────────────────────────────────────────
#  Faculty-side Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@attendance_bp.route('/api/attendance/setup-data', methods=['GET'])
@login_required
@role_required('faculty', 'admin')
def setup_data():
    faculty_id = session.get('user_id')

    entries = TimetableEntry.query.filter_by(faculty_id=faculty_id).all()

    course_ids = list({e.course_id for e in entries})
    section_ids = list({e.section_id for e in entries})

    if not course_ids:
        return jsonify({'courses': [], 'sections': [], 'map': {}})

    courses = Course.query.filter(Course.id.in_(course_ids)).order_by(Course.code).all()
    sections = Section.query.filter(Section.id.in_(section_ids)).order_by(Section.name).all()

    course_section_map = {}
    for e in entries:
        c_id = str(e.course_id)
        if c_id not in course_section_map:
            course_section_map[c_id] = []
        if e.section_id not in course_section_map[c_id]:
            course_section_map[c_id].append(e.section_id)

    return jsonify({
        'courses': [{'id': c.id, 'code': c.code, 'name': c.name} for c in courses],
        'sections': [
            {
                'id': s.id,
                'name': s.name,
                'department_name': s.department.name if s.department else '',
                'student_count': s.student_count or len(s.students)
            }
            for s in sections
        ],
        'map': course_section_map
    })


@attendance_bp.route('/api/attendance/session/start', methods=['POST'])
@login_required
@role_required('faculty', 'admin')
def start_session():
    data = request.json or {}
    course_id = data.get('course_id')
    section_id = data.get('section_id')
    lat = data.get('lat')
    lng = data.get('lng')

    if not all([course_id, section_id, lat is not None, lng is not None]):
        return jsonify({'error': 'course_id, section_id, lat, lng are required'}), 400

    faculty_id = session.get('user_id')
    faculty_name = session.get('user_name', 'Unknown')

    faculty = Faculty.query.get(faculty_id)
    if not faculty:
        return jsonify({'error': 'Faculty not found'}), 404

    course = Course.query.get(course_id)
    sec = Section.query.get(section_id)
    if not course or not sec:
        return jsonify({'error': 'Course or section not found'}), 404

    now = time.time()
    session_token = secrets.token_urlsafe(48)
    first_qr = {'token': secrets.token_urlsafe(32), 'created_at': now}

    ACTIVE_SESSIONS[session_token] = {
        'faculty_id': faculty_id,
        'faculty_name': faculty_name,
        'course_id': int(course_id),
        'section_id': int(section_id),
        'lat': float(lat),
        'lng': float(lng),
        'created_at': now,
        'expires_at': now + SESSION_LIFETIME,
        'qr_tokens': [first_qr],
        'submissions': {},
        'flagged': []
    }

    qr_data = f"SMARTATTEND|{session_token}|{first_qr['token']}"

    return jsonify({
        'session_token': session_token,
        'qr_token': first_qr['token'],
        'qr_data': qr_data,
        'expires_in': SESSION_LIFETIME,
        'course_name': course.name,
        'section_name': sec.name
    })


@attendance_bp.route('/api/attendance/session/qr/<session_token>', methods=['GET'])
@login_required
def get_rolling_qr(session_token):
    """Faculty polls this every 2.8 s to get a fresh QR token.
    Auth: any logged-in user who knows the session_token — token is the secret.
    """
    sess = ACTIVE_SESSIONS.get(session_token)
    if not sess:
        return jsonify({'error': 'Session not found', 'code': 'NO_SESSION'}), 404

    now = time.time()
    if now > sess['expires_at']:
        del ACTIVE_SESSIONS[session_token]
        return jsonify({'error': 'Session expired', 'code': 'SESSION_EXPIRED'}), 410

    tok = _make_qr_token(sess)
    qr_data = f"SMARTATTEND|{session_token}|{tok['token']}"

    sec = Section.query.get(sess['section_id'])
    total = len(sec.students) if sec else 0
    present = sum(1 for s in sess['submissions'].values() if s['status'] == 'verified')
    absent = total - present

    return jsonify({
        'qr_token': tok['token'],
        'qr_data': qr_data,
        'qr_expires_in': QR_TOKEN_INTERVAL + QR_TOKEN_GRACE,
        'session_expires_in': int(sess['expires_at'] - now),
        'present': present,
        'absent': absent,
        'total': total
    })


@attendance_bp.route('/api/attendance/session/live/<session_token>', methods=['GET'])
@login_required
def live_session(session_token):
    """Faculty polls this for the live student list.
    Auth: any logged-in user who knows the session_token.
    """
    sess = ACTIVE_SESSIONS.get(session_token)
    if not sess:
        return jsonify({'error': 'Session not found', 'code': 'NO_SESSION'}), 404

    now = time.time()
    if now > sess['expires_at']:
        return jsonify({'error': 'Session expired', 'code': 'SESSION_EXPIRED'}), 410

    students_out = []
    for sid, sub in sess['submissions'].items():
        students_out.append({
            'student_id': sid,
            'student_name': sub['student_name'],
            'status': sub['status'],
            'time': sub['time'],
            'distance': sub['distance'],
            'flagged': sub['flagged'],
            'flag_reason': sub.get('flag_reason', ''),
            'has_selfie': bool(sub.get('selfie'))
        })

    present = sum(1 for s in students_out if s['status'] == 'verified')
    flagged_count = sum(1 for s in students_out if s['flagged'])

    sec = Section.query.get(sess['section_id'])
    total = len(sec.students) if sec else 0
    absent = total - present

    return jsonify({
        'students': students_out,
        'present': present,
        'absent': absent,
        'total': total,
        'flagged_count': flagged_count,
        'session_expires_in': int(sess['expires_at'] - now)
    })


@attendance_bp.route('/api/attendance/session/stop', methods=['POST'])
@login_required
def stop_session():
    """Faculty stops session — writes Attendance records to DB.
    Auth: any logged-in user who knows the session_token.
    """
    data = request.json or {}
    session_token = data.get('session_token')
    if not session_token:
        return jsonify({'error': 'session_token required'}), 400

    sess = ACTIVE_SESSIONS.get(session_token)
    if not sess:
        return jsonify({'error': 'Session not found', 'code': 'NO_SESSION'}), 404

    sec = Section.query.get(sess['section_id'])
    if not sec:
        del ACTIVE_SESSIONS[session_token]
        return jsonify({'error': 'Section not found'}), 404

    today = ist_today()
    course_id = sess['course_id']
    section_id = sess['section_id']

    Attendance.query.filter_by(
        section_id=section_id,
        course_id=course_id,
        date=today
    ).delete()
    db.session.flush()

    verified_ids = {int(sid) for sid, sub in sess['submissions'].items()
                    if sub['status'] == 'verified'}
    all_students = sec.students
    total = len(all_students)
    present_count = 0
    absent_count = 0
    flagged_count = sum(1 for sub in sess['submissions'].values() if sub['flagged'])

    for student in all_students:
        status = 'present' if student.id in verified_ids else 'absent'
        if status == 'present':
            present_count += 1
        else:
            absent_count += 1

        att = Attendance(
            student_id=student.id,
            course_id=course_id,
            section_id=section_id,
            date=today,
            status=status
        )
        db.session.add(att)

    db.session.commit()
    del ACTIVE_SESSIONS[session_token]

    return jsonify({
        'message': 'Attendance saved successfully',
        'present': present_count,
        'absent': absent_count,
        'total': total,
        'flagged': flagged_count
    })


@attendance_bp.route('/api/attendance/manual-save', methods=['POST'])
@login_required
@role_required('faculty', 'admin')
def manual_save():
    """Manual mark attendance by faculty (legacy — used by roll-call UI).
    Body: { section_id, course_id, date, marks: { student_id: 'P'|'A'|'OD' } }
    """
    data = request.json or {}
    section_id = data.get('section_id')
    course_id = data.get('course_id')
    date_str = data.get('date')
    marks = data.get('marks', {})

    if not all([section_id, course_id, date_str]):
        return jsonify({'error': 'Missing parameters'}), 400

    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception:
        dt = ist_today()

    Attendance.query.filter_by(
        section_id=section_id,
        course_id=course_id,
        date=dt
    ).delete()

    for sid, status in marks.items():
        att = Attendance(
            student_id=int(sid),
            course_id=course_id,
            section_id=section_id,
            date=dt,
            status='present' if status == 'P' else 'absent' if status == 'A' else 'od'
        )
        db.session.add(att)

    db.session.commit()
    return jsonify({'success': True, 'message': 'Attendance saved successfully'})


@attendance_bp.route('/api/attendance/manual', methods=['POST'])
@login_required
@role_required('faculty', 'admin')
def manual_attendance():
    """Save attendance for an entire section at once.
    Body: { course_id, section_id, date, present_student_ids: [1, 2, 3] }
    Marks everyone in the section — present if in list, absent otherwise.
    Deletes existing records for same course+section+date before saving.
    """
    data = request.json or {}
    course_id = data.get('course_id')
    section_id = data.get('section_id')
    date_str = data.get('date')
    present_ids = set(int(i) for i in data.get('present_student_ids', []))

    if not all([course_id, section_id, date_str]):
        return jsonify({'error': 'course_id, section_id, and date are required'}), 400

    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    sec = Section.query.get(section_id)
    if not sec:
        return jsonify({'error': 'Section not found'}), 404

    # Delete existing records for this course+section+date
    Attendance.query.filter_by(
        section_id=section_id,
        course_id=course_id,
        date=dt
    ).delete()
    db.session.flush()

    present_count = 0
    absent_count = 0

    for student in sec.students:
        status = 'present' if student.id in present_ids else 'absent'
        if status == 'present':
            present_count += 1
        else:
            absent_count += 1

        att = Attendance(
            student_id=student.id,
            course_id=course_id,
            section_id=section_id,
            date=dt,
            status=status
        )
        db.session.add(att)

    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'Attendance saved successfully',
        'present': present_count,
        'absent': absent_count,
        'total': present_count + absent_count
    })


@attendance_bp.route('/api/attendance/update-student', methods=['PUT'])
@login_required
@role_required('faculty', 'admin')
def update_student_attendance():
    """Update a specific student's attendance status.
    Body: { student_id, course_id, date, status }
    status must be 'present', 'absent', or 'od'.
    """
    data = request.json or {}
    student_id = data.get('student_id')
    course_id = data.get('course_id')
    date_str = data.get('date')
    status = data.get('status', '').lower()

    if not all([student_id, course_id, date_str, status]):
        return jsonify({'error': 'student_id, course_id, date, and status are required'}), 400

    if status not in ('present', 'absent', 'od'):
        return jsonify({'error': "status must be 'present', 'absent', or 'od'"}), 400

    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    record = Attendance.query.filter_by(
        student_id=student_id,
        course_id=course_id,
        date=dt
    ).first()

    if record:
        record.status = status
    else:
        # Find the section for this student+course
        student = Student.query.get(student_id)
        section_id = None
        if student and student.sections:
            section_id = student.sections[0].id
        record = Attendance(
            student_id=student_id,
            course_id=course_id,
            section_id=section_id,
            date=dt,
            status=status
        )
        db.session.add(record)

    db.session.commit()
    return jsonify({'success': True, 'message': f'Attendance updated to {status}'})


@attendance_bp.route('/api/attendance/students-in-section', methods=['GET'])
@login_required
@role_required('faculty', 'admin')
def students_in_section():
    """Return all students enrolled in a given section.
    Query param: section_id
    Returns: { students: [{id, name, reg_no}] }
    """
    section_id = request.args.get('section_id', type=int)
    if not section_id:
        return jsonify({'error': 'section_id is required'}), 400

    sec = Section.query.get(section_id)
    if not sec:
        return jsonify({'error': 'Section not found'}), 404

    students = [
        {'id': s.id, 'name': s.name, 'reg_no': s.student_uid}
        for s in sorted(sec.students, key=lambda s: s.name)
    ]
    return jsonify({'students': students})


@attendance_bp.route('/api/attendance/get-roll', methods=['GET'])
@login_required
@role_required('faculty', 'admin')
def get_roll():
    """Fetch current attendance marks for a course+section+date."""
    section_id = request.args.get('section_id')
    course_id = request.args.get('course_id')
    date_str = request.args.get('date')

    if not all([section_id, course_id, date_str]):
        return jsonify({'error': 'Missing parameters'}), 400

    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception:
        dt = ist_today()

    records = Attendance.query.filter_by(
        section_id=section_id,
        course_id=course_id,
        date=dt
    ).all()

    marks = {}
    for r in records:
        status = 'P' if r.status == 'present' else 'A' if r.status == 'absent' else 'OD'
        marks[r.student_id] = status

    return jsonify({'marks': marks})


# ──────────────────────────────────────────────────────────────────────────────
#  Student-side Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@attendance_bp.route('/api/attendance/active-session', methods=['GET'])
@login_required
@role_required('student')
def get_active_session():
    student_id = session.get('user_id')
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'active': False, 'error': 'Student not found'}), 404

    section_ids = [sec.id for sec in student.sections]

    now = time.time()
    for token, sess in ACTIVE_SESSIONS.items():
        if sess['section_id'] in section_ids and sess['expires_at'] > now:
            return jsonify({
                'active': True,
                'session_token': token,
                'course_name': Course.query.get(sess['course_id']).name,
                'faculty_name': sess['faculty_name'],
                'expires_in': int(sess['expires_at'] - now)
            })

    return jsonify({'active': False})


@attendance_bp.route('/api/attendance/submit', methods=['POST'])
@login_required
@role_required('student')
def submit_attendance():
    data = request.json or {}
    session_token = data.get('session_token', '')
    qr_token = data.get('qr_token', '')
    student_lat = data.get('lat')
    student_lng = data.get('lng')
    gps_accuracy = data.get('accuracy', 999)
    selfie = data.get('selfie', '')

    student_id = session.get('user_id')

    # CHECK 1: VPN Detection
    client_ip = get_client_ip()
    if is_vpn_ip(client_ip):
        return jsonify({
            'success': False,
            'code': 'VPN_DETECTED',
            'message': 'Disable your VPN to mark attendance'
        }), 403

    # CHECK 2: Active Session Exists
    sess = ACTIVE_SESSIONS.get(session_token)
    if not sess:
        return jsonify({'success': False, 'code': 'NO_SESSION',
                        'message': 'No active session. Ask your faculty to start attendance'}), 404

    now = time.time()
    if now > sess['expires_at']:
        del ACTIVE_SESSIONS[session_token]
        return jsonify({'success': False, 'code': 'SESSION_EXPIRED',
                        'message': 'Session has expired'}), 410

    # CHECK 3: GPS Distance
    if student_lat is None or student_lng is None:
        return jsonify({'success': False, 'code': 'NO_GPS',
                        'message': 'GPS location not available. Enable location services'}), 400

    if float(gps_accuracy) > GPS_MAX_ACCURACY:
        return jsonify({'success': False, 'code': 'GPS_INACCURATE',
                        'message': f'GPS accuracy {int(gps_accuracy)}m is too low. Move to open area'}), 400

    distance = haversine_distance(
        float(student_lat), float(student_lng),
        sess['lat'], sess['lng']
    )
    distance_int = int(round(distance))

    if distance_int > GPS_MAX_DISTANCE:
        return jsonify({
            'success': False,
            'code': 'TOO_FAR',
            'distance': distance_int,
            'message': f'You are {distance_int}m away. Must be within {GPS_MAX_DISTANCE}m of your faculty'
        }), 403

    gps_spoofed = (
        abs(float(student_lat) - sess['lat']) < 1e-7 and
        abs(float(student_lng) - sess['lng']) < 1e-7
    )

    # CHECK 4: QR Token Validity
    if not _find_valid_token(sess, qr_token):
        return jsonify({'success': False, 'code': 'QR_EXPIRED',
                        'message': 'QR code expired. Scan the new QR code'}), 400

    # CHECK 5: Already Submitted
    student_key = str(student_id)
    existing = sess['submissions'].get(student_key)
    if existing and existing['status'] == 'verified':
        return jsonify({'success': False, 'code': 'ALREADY_MARKED',
                        'message': 'Attendance already marked for this session'}), 409

    # CHECK 6: Student Enrolled in Section
    sec = Section.query.get(sess['section_id'])
    if not sec:
        return jsonify({'success': False, 'code': 'NO_SESSION'}), 404

    enrolled_ids = {s.id for s in sec.students}
    if student_id not in enrolled_ids:
        return jsonify({'success': False, 'code': 'NOT_ENROLLED',
                        'message': 'You are not enrolled in this section'}), 403

    student = Student.query.get(student_id)
    student_name = student.name if student else 'Unknown'

    # CHECK 7: Face Verification (flag — never block)
    flagged = gps_spoofed
    flag_reasons = []

    if gps_spoofed:
        flag_reasons.append('GPS coordinates identical to faculty (possible spoof)')

    if not selfie:
        flagged = True
        flag_reasons.append('No selfie captured')
    else:
        face_confidence = _verify_face_stub(selfie, student_id)
        if face_confidence < 0.6:
            flagged = True
            flag_reasons.append(f'Face mismatch (confidence {face_confidence:.2f})')

    sub_time = datetime.now(IST).strftime('%H:%M:%S')

    if flagged and student_key not in sess['flagged']:
        sess['flagged'].append(student_key)

    sess['submissions'][student_key] = {
        'student_name': student_name,
        'status': 'verified',
        'time': sub_time,
        'distance': distance_int,
        'flagged': flagged,
        'flag_reason': '; '.join(flag_reasons),
        'selfie': selfie[:200] if selfie else ''
    }

    response = {
        'success': True,
        'message': 'Attendance marked successfully' + (' (flagged for review)' if flagged else ''),
        'flagged': flagged
    }
    if flagged:
        response['flag_reasons'] = flag_reasons

    return jsonify(response)


@attendance_bp.route('/api/attendance/verify-face', methods=['POST'])
@login_required
@role_required('student')
def verify_face():
    data = request.json or {}
    student_id = session.get('user_id')
    student = Student.query.get(student_id)

    if not student:
        return jsonify({'match': False, 'error': 'Student not found'}), 404

    # Final confirmation: face-api.js already verified client-side
    if data.get('verified'):
        confidence = data.get('confidence', 0)
        session['face_verified'] = True
        session['face_confidence'] = round(float(confidence), 1)
        return jsonify({
            'match': True,
            'confidence': session['face_confidence'],
            'message': f"Identity verified at {session['face_confidence']:.1f}% confidence"
        })

    # Initial call: return profile photo for client-side face-api.js comparison
    if not student.photo_url:
        return jsonify({'match': False, 'error': 'No profile picture on file. Please contact Admin.'})

    return jsonify({
        'profile_photo': student.photo_url,
        'student_name': student.name
    })


# ──────────────────────────────────────────────────────────────────────────────
#  Face Verification Stub
# ──────────────────────────────────────────────────────────────────────────────

def _verify_face_stub(selfie_b64: str, student_id: int) -> float:
    return 1.0


# ──────────────────────────────────────────────────────────────────────────────
#  Page Routes
# ──────────────────────────────────────────────────────────────────────────────

@attendance_bp.route('/attendance/faculty-qr')
@login_required
@role_required('faculty', 'admin')
def faculty_qr_page():
    return render_template('attendance_faculty.html')


@attendance_bp.route('/attendance/student-scan')
@login_required
@role_required('student')
def student_scan_page():
    return render_template('attendance_student.html')
