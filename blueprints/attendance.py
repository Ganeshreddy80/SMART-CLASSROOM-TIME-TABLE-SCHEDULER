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
On session stop, data is committed to SQLite Attendance table.
"""

import math
import os
import secrets
import time
import ipaddress
from datetime import date as date_type

from flask import Blueprint, request, jsonify, session, render_template

from models import db, Student, Faculty, Course, Section, Attendance, TimetableEntry
from blueprints.utils import login_required, role_required

attendance_bp = Blueprint('attendance_bp', __name__)

# ─── In-memory Session Store ─────────────────────────────────────────────────
# Structure documented in system overview (see docstring above)
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
    # Cloudflare WARP / 1.1.1.1 VPN
    "104.16.0.0/12",
    "172.64.0.0/13",
    "162.158.0.0/15",
    # Mullvad
    "193.138.218.0/24",
    "185.213.154.0/23",
    # NordVPN representative blocks
    "80.240.0.0/13",
    "5.180.0.0/14",
    # ProtonVPN
    "185.159.156.0/22",
    "185.107.80.0/22",
    # ExpressVPN
    "205.185.208.0/20",
    # Common datacenter / hosting (AWS, GCP, Azure, DigitalOcean, Linode)
    "3.0.0.0/9",
    "13.32.0.0/12",
    "34.0.0.0/10",
    "35.184.0.0/13",
    "40.74.0.0/14",
    "52.0.0.0/11",
    "54.160.0.0/11",
    "104.196.0.0/14",
    "107.178.192.0/18",
    "130.211.0.0/16",
    "139.59.0.0/16",
    "142.93.0.0/16",
    "159.203.0.0/16",
    "165.22.0.0/15",
    "167.71.0.0/16",
    "167.99.0.0/16",
]

_VPN_NETWORKS = [ipaddress.ip_network(cidr, strict=False) for cidr in _VPN_RANGES]


def is_vpn_ip(ip_str: str) -> bool:
    """Return True if ip_str falls in a known VPN / datacenter CIDR."""
    try:
        addr = ipaddress.ip_address(ip_str)
        # RFC-1918 private ranges are always local — never flag as VPN
        if addr.is_private or addr.is_loopback:
            return False
        for net in _VPN_NETWORKS:
            if addr in net:
                return True
    except ValueError:
        pass
    return False


def get_client_ip() -> str:
    """Extract real client IP, honouring X-Forwarded-For."""
    xff = request.headers.get('X-Forwarded-For', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.remote_addr or '0.0.0.0'


def _purge_old_tokens(sess: dict) -> None:
    """Remove QR tokens older than QR_TOKEN_INTERVAL + QR_TOKEN_GRACE seconds."""
    cutoff = time.time() - (QR_TOKEN_INTERVAL + QR_TOKEN_GRACE)
    sess['qr_tokens'] = [t for t in sess['qr_tokens'] if t['created_at'] >= cutoff]
    # Also cap the list to history limit
    if len(sess['qr_tokens']) > QR_HISTORY_LIMIT:
        sess['qr_tokens'] = sess['qr_tokens'][-QR_HISTORY_LIMIT:]


def _make_qr_token(sess: dict) -> dict:
    """Generate a fresh QR token, append to session, and return it."""
    tok = {
        'token': secrets.token_urlsafe(32),
        'created_at': time.time()
    }
    sess['qr_tokens'].append(tok)
    _purge_old_tokens(sess)
    return tok


def _find_valid_token(sess: dict, qr_token: str) -> bool:
    """Check whether qr_token exists and is within the valid window."""
    now = time.time()
    cutoff = now - (QR_TOKEN_INTERVAL + QR_TOKEN_GRACE)
    for t in sess['qr_tokens']:
        if t['token'] == qr_token and t['created_at'] >= cutoff:
            return True
    return False


def _faculty_session_for_student(section_id: int) -> tuple[str | None, dict | None]:
    """Return (session_token, session_dict) for the first active session whose
    section_id matches. Returns (None, None) if none found."""
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
    """Returns ONLY courses + sections that the current faculty is teaching.
    Includes a mapping to filter sections based on selected course.
    """
    faculty_id = session.get('user_id')
    
    # Get all timetable entries for this faculty
    entries = TimetableEntry.query.filter_by(faculty_id=faculty_id).all()
    
    course_ids = list({e.course_id for e in entries})
    section_ids = list({e.section_id for e in entries})
    
    if not course_ids:
        return jsonify({'courses': [], 'sections': [], 'map': {}})

    courses = Course.query.filter(Course.id.in_(course_ids)).order_by(Course.code).all()
    sections = Section.query.filter(Section.id.in_(section_ids)).order_by(Section.name).all()
    
    # Create a mapping of course_id -> [section_ids]
    course_section_map = {}
    for e in entries:
        c_id = str(e.course_id)
        if c_id not in course_section_map:
            course_section_map[c_id] = []
        if e.section_id not in course_section_map[c_id]:
            course_section_map[c_id].append(e.section_id)

    return jsonify({
        'courses': [
            {'id': c.id, 'code': c.code, 'name': c.name}
            for c in courses
        ],
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
    """Faculty starts an attendance session.
    Body: { course_id, section_id, lat, lng }
    Returns: { session_token, qr_data, qr_token, expires_in }
    """
    data = request.json or {}
    course_id = data.get('course_id')
    section_id = data.get('section_id')
    lat = data.get('lat')
    lng = data.get('lng')

    if not all([course_id, section_id, lat is not None, lng is not None]):
        return jsonify({'error': 'course_id, section_id, lat, lng are required'}), 400

    faculty_id = session.get('user_id')
    faculty_name = session.get('user_name', 'Unknown')

    # Validate faculty exists
    faculty = Faculty.query.get(faculty_id)
    if not faculty:
        return jsonify({'error': 'Faculty not found'}), 404

    # Validate course & section exist
    course = Course.query.get(course_id)
    section = Section.query.get(section_id)
    if not course or not section:
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
        'section_name': section.name
    })


@attendance_bp.route('/api/attendance/session/qr/<session_token>', methods=['GET'])
@login_required
@role_required('faculty', 'admin')
def get_rolling_qr(session_token):
    """Faculty polls this every 2.8 seconds to get a fresh QR token.
    Returns: { qr_token, qr_data, qr_expires_in, session_expires_in, present, total, absent }
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

    section = Section.query.get(sess['section_id'])
    total = len(section.students) if section else 0
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
@role_required('faculty', 'admin')
def live_session(session_token):
    """Faculty polls this for the live student list (every 3 seconds).
    Returns: { students: [...], present, absent, flagged_count }
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

    section = Section.query.get(sess['section_id'])
    total = len(section.students) if section else 0
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
@role_required('faculty', 'admin')
def stop_session():
    """Faculty stops session — writes Attendance records to DB.
    Body: { session_token }
    Returns: { present, absent, total, flagged }
    """
    data = request.json or {}
    session_token = data.get('session_token')
    if not session_token:
        return jsonify({'error': 'session_token required'}), 400

    sess = ACTIVE_SESSIONS.get(session_token)
    if not sess:
        return jsonify({'error': 'Session not found', 'code': 'NO_SESSION'}), 404



    section = Section.query.get(sess['section_id'])
    if not section:
        del ACTIVE_SESSIONS[session_token]
        return jsonify({'error': 'Section not found'}), 404

    today = date_type.today()
    course_id = sess['course_id']
    section_id = sess['section_id']

    # Rule 8: Delete existing records for same section+course+date before inserting
    Attendance.query.filter_by(
        section_id=section_id,
        course_id=course_id,
        date=today
    ).delete()
    db.session.flush()

    verified_ids = {int(sid) for sid, sub in sess['submissions'].items()
                    if sub['status'] == 'verified'}
    all_students = section.students
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

    # Clean up session
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
    """Manual mark attendance by faculty.
    Body: { section_id, course_id, date, marks: { student_id: status } }
    """
    data = request.json or {}
    section_id = data.get('section_id')
    course_id = data.get('course_id')
    date_str = data.get('date')
    marks = data.get('marks', {})

    if not all([section_id, course_id, date_str]):
        return jsonify({'error': 'Missing parameters'}), 400

    try:
        from datetime import datetime as _dt_
        dt = _dt_.strptime(date_str, '%Y-%m-%d').date()
    except:
        dt = date_type.today()

    # Overwrite existing for this specific session
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


@attendance_bp.route('/api/attendance/get-roll', methods=['GET'])
@login_required
@role_required('faculty', 'admin')
def get_roll():
    """Fetch current attendance marks for a session."""
    section_id = request.args.get('section_id')
    course_id = request.args.get('course_id')
    date_str = request.args.get('date')

    if not all([section_id, course_id, date_str]):
        return jsonify({'error': 'Missing parameters'}), 400

    try:
        from datetime import datetime as _dt_
        dt = _dt_.strptime(date_str, '%Y-%m-%d').date()
    except:
        dt = date_type.today()

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
    """Student checks if there's an active session for their section."""
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
    """Student submits attendance — runs all 7 checks in order.
    Body: { session_token, qr_token, lat, lng, accuracy, selfie }
    """
    data = request.json or {}
    session_token = data.get('session_token', '')
    qr_token = data.get('qr_token', '')
    student_lat = data.get('lat')
    student_lng = data.get('lng')
    gps_accuracy = data.get('accuracy', 999)
    selfie = data.get('selfie', '')

    student_id = session.get('user_id')

    # ── CHECK 1: VPN Detection ────────────────────────────────
    client_ip = get_client_ip()
    if is_vpn_ip(client_ip):
        return jsonify({
            'success': False,
            'code': 'VPN_DETECTED',
            'message': 'Disable your VPN to mark attendance'
        }), 403

    # ── CHECK 2: Active Session Exists ────────────────────────
    sess = ACTIVE_SESSIONS.get(session_token)
    if not sess:
        return jsonify({'success': False, 'code': 'NO_SESSION',
                        'message': 'No active session. Ask your faculty to start attendance'}), 404

    now = time.time()
    if now > sess['expires_at']:
        del ACTIVE_SESSIONS[session_token]
        return jsonify({'success': False, 'code': 'SESSION_EXPIRED',
                        'message': 'Session has expired'}), 410

    # ── CHECK 3: GPS Distance ─────────────────────────────────
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

    # Rule 10: GPS perfect match → flag as potential spoof
    gps_spoofed = (
        abs(float(student_lat) - sess['lat']) < 1e-7 and
        abs(float(student_lng) - sess['lng']) < 1e-7
    )

    # ── CHECK 4: QR Token Validity ────────────────────────────
    if not _find_valid_token(sess, qr_token):
        return jsonify({'success': False, 'code': 'QR_EXPIRED',
                        'message': 'QR code expired. Scan the new QR code'}), 400

    # ── CHECK 5: Already Submitted ────────────────────────────
    student_key = str(student_id)
    existing = sess['submissions'].get(student_key)
    if existing and existing['status'] == 'verified':
        return jsonify({'success': False, 'code': 'ALREADY_MARKED',
                        'message': 'Attendance already marked for this session'}), 409

    # ── CHECK 6: Student Enrolled in Section ─────────────────
    section = Section.query.get(sess['section_id'])
    if not section:
        return jsonify({'success': False, 'code': 'NO_SESSION'}), 404

    enrolled_ids = {s.id for s in section.students}
    if student_id not in enrolled_ids:
        return jsonify({'success': False, 'code': 'NOT_ENROLLED',
                        'message': 'You are not enrolled in this section'}), 403

    student = Student.query.get(student_id)
    student_name = student.name if student else 'Unknown'

    # ── CHECK 7: Face Verification (flag — never block) ───────
    flagged = gps_spoofed  # carry over GPS spoof flag
    flag_reasons = []

    if gps_spoofed:
        flag_reasons.append('GPS coordinates identical to faculty (possible spoof)')

    if not selfie:
        flagged = True
        flag_reasons.append('No selfie captured')
    else:
        # Production: deepface / face_recognition comparison against registered photo
        # Stub: always pass with simulated confidence (replace with real logic)
        face_confidence = _verify_face_stub(selfie, student_id)
        if face_confidence < 0.6:
            flagged = True
            flag_reasons.append(f'Face mismatch (confidence {face_confidence:.2f})')

    # ── All checks passed — record submission ─────────────────
    import datetime as _dt
    sub_time = _dt.datetime.now().strftime('%H:%M:%S')

    if student_key in sess['flagged'] and flagged:
        pass  # already in flagged list

    if flagged and student_key not in sess['flagged']:
        sess['flagged'].append(student_key)

    sess['submissions'][student_key] = {
        'student_name': student_name,
        'status': 'verified',          # submission is accepted; flagged is a separate concern
        'time': sub_time,
        'distance': distance_int,
        'flagged': flagged,
        'flag_reason': '; '.join(flag_reasons),
        'selfie': selfie[:200] if selfie else ''  # truncate — full selfie stored in memory only
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
    import base64, requests as req

    data = request.json or {}
    selfie_b64 = data.get('selfie')
    if not selfie_b64:
        return jsonify({'match': False, 'error': 'No selfie provided'}), 400

    student_id = session.get('user_id')
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'match': False, 'error': 'Student not found'}), 404
    if not student.photo_url:
        return jsonify({'match': False, 'error': 'No profile picture found. Contact Admin.'})

    try:
        # Clean base64 selfie
        selfie_data = selfie_b64.split(',')[1] if ',' in selfie_b64 else selfie_b64
        profile_data = student.photo_url.split(',')[1] if ',' in student.photo_url else student.photo_url

        # Call Face++ compare API
        response = req.post(
            'https://api-us.faceplusplus.com/facepp/v3/compare',
            data={
                'api_key': os.environ.get('FACEPP_API_KEY'),
                'api_secret': os.environ.get('FACEPP_API_SECRET'),
                'image_base64_1': selfie_data,
                'image_base64_2': profile_data
            },
            timeout=15
        )
        result = response.json()

        if 'error_message' in result:
            return jsonify({'match': False, 'error': result['error_message']}), 500

        confidence = round(result.get('confidence', 0), 1)
        is_match = confidence >= 75

        if is_match:
            return jsonify({'match': True, 'confidence': confidence, 'message': 'Face verified!'})
        else:
            return jsonify({'match': False, 'confidence': confidence, 'error': 'Face does not match profile.'})

    except Exception as e:
        return jsonify({'match': False, 'error': f'Verification error: {str(e)}'}), 500

# ──────────────────────────────────────────────────────────────────────────────
#  Face Verification Stub
# ──────────────────────────────────────────────────────────────────────────────

def _verify_face_stub(selfie_b64: str, student_id: int) -> float:
    """Stub face verifier.  In production, compare selfie_b64 against the
    student's registered photo using deepface or face_recognition.
    Returns confidence in [0.0, 1.0].
    """
    # TODO: integrate deepface
    #   from deepface import DeepFace
    #   result = DeepFace.verify(selfie_b64, registered_photo_path, model_name='Facenet512')
    #   return 1.0 - result['distance']  (map distance to confidence)

    # Stub: return 1.0 (perfect match) — change to 0.0 to test flagging
    return 1.0


# ──────────────────────────────────────────────────────────────────────────────
#  Page Routes (served HTML pages for faculty QR display & student scanner)
# ──────────────────────────────────────────────────────────────────────────────

@attendance_bp.route('/attendance/faculty-qr')
@login_required
@role_required('faculty', 'admin')
def faculty_qr_page():
    """Serve the Faculty QR Session page."""
    return render_template('attendance_faculty.html')


@attendance_bp.route('/attendance/student-scan')
@login_required
@role_required('student')
def student_scan_page():
    """Serve the Student QR Scanner page."""
    return render_template('attendance_student.html')
