from flask_sqlalchemy import SQLAlchemy
import json, re, secrets
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


def generate_email_from_name(name):
    """Generate email in format firstname.lastname@srmap.edu.in from a full name."""
    # Remove titles like Dr., Prof., Mr., Mrs., etc.
    cleaned = re.sub(r'^(Dr\.?|Prof\.?|Mr\.?|Mrs\.?|Ms\.?)\s+', '', name.strip(), flags=re.IGNORECASE)
    parts = cleaned.strip().split()
    if len(parts) >= 2:
        email_local = f"{parts[0].lower()}.{parts[-1].lower()}"
    elif len(parts) == 1:
        email_local = parts[0].lower()
    else:
        email_local = 'user'
    # Remove any non-alphanumeric chars except dot
    email_local = re.sub(r'[^a-z0-9.]', '', email_local)
    return f"{email_local}@srmap.edu.in"


def generate_default_password(name):
    """Generate default password in format firstname@123."""
    cleaned = re.sub(r'^(Dr\.?|Prof\.?|Mr\.?|Mrs\.?|Ms\.?)\s+', '', name.strip(), flags=re.IGNORECASE)
    parts = cleaned.strip().split()
    firstname = parts[0].lower() if parts else 'user'
    firstname = re.sub(r'[^a-z0-9]', '', firstname)
    return f"{firstname}@123"


def ensure_unique_email(email, exclude_faculty_id=None, exclude_student_id=None):
    """Check if email is unique across Faculty and Student tables. If not, append a number."""
    base_local, domain = email.split('@')
    candidate = email
    counter = 2
    while True:
        fac_query = Faculty.query.filter_by(email=candidate)
        stu_query = Student.query.filter_by(email=candidate)
        if exclude_faculty_id:
            fac_query = fac_query.filter(Faculty.id != exclude_faculty_id)
        if exclude_student_id:
            stu_query = stu_query.filter(Student.id != exclude_student_id)
        if not fac_query.first() and not stu_query.first():
            return candidate
        candidate = f"{base_local}{counter}@{domain}"
        counter += 1

# --- Association Tables ---
faculty_courses = db.Table('faculty_courses',
    db.Column('faculty_id', db.Integer, db.ForeignKey('faculty.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('course.id'), primary_key=True)
)

student_courses = db.Table('student_courses',
    db.Column('student_id', db.Integer, db.ForeignKey('student.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('course.id'), primary_key=True)
)

section_students = db.Table('section_students',
    db.Column('section_id', db.Integer, db.ForeignKey('section.id'), primary_key=True),
    db.Column('student_id', db.Integer, db.ForeignKey('student.id'), primary_key=True)
)


class University(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, default='My University')
    total_blocks = db.Column(db.Integer, default=2)
    floors_per_block = db.Column(db.Text)
    rooms_per_block = db.Column(db.Integer, default=5)
    room_capacity = db.Column(db.Integer, default=60)
    days = db.Column(db.Text, default='["Monday","Tuesday","Wednesday","Thursday","Friday"]')
    timeslots = db.Column(db.Text, default='["9:00-10:00","10:00-11:00","11:00-12:00","12:00-1:00","2:00-3:00","3:00-4:00","4:00-5:00"]')

    def get_days(self):
        return json.loads(self.days) if self.days else []

    def get_timeslots(self):
        return json.loads(self.timeslots) if self.timeslots else []

    def get_floors_per_block(self):
        try:
            return json.loads(self.floors_per_block) if self.floors_per_block else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'total_blocks': self.total_blocks,
            'floors_per_block': self.get_floors_per_block(),
            'rooms_per_block': self.rooms_per_block,
            'room_capacity': self.room_capacity,
            'days': self.get_days(),
            'timeslots': self.get_timeslots()
        }


class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False, unique=True)
    courses = db.relationship('Course', backref='department', lazy=True, cascade='all, delete-orphan')
    faculty = db.relationship('Faculty', backref='department', lazy=True)
    students = db.relationship('Student', backref='department', lazy=True)
    sections = db.relationship('Section', backref='department', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code
        }


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    credits = db.Column(db.Integer, nullable=False, default=3)
    difficulty = db.Column(db.String(20), nullable=False, default='Medium')  # Hard, Medium, Easy
    classes_per_week = db.Column(db.Integer, nullable=False, default=4)
    course_type = db.Column(db.String(20), nullable=False, default='Theory')  # Theory, Lab

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else '',
            'credits': self.credits,
            'difficulty': self.difficulty,
            'classes_per_week': self.classes_per_week,
            'course_type': self.course_type
        }


class Faculty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    faculty_uid = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=True, unique=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    available_slots = db.Column(db.Text, default='{}')  # JSON: {"Monday": ["9:00-10:00", ...], ...}
    password_hash = db.Column(db.String(255), nullable=True)
    photo_url = db.Column(db.Text, nullable=True)
    courses_can_teach = db.relationship('Course', secondary=faculty_courses, lazy='subquery',
                                         backref=db.backref('faculty_members', lazy=True))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        if not self.password_hash: return False
        return check_password_hash(self.password_hash, password)

    def get_available_slots(self):
        return json.loads(self.available_slots) if self.available_slots else {}

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_uid': self.faculty_uid,
            'name': self.name,
            'email': self.email or '',
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else '',
            'courses_can_teach': [c.id for c in self.courses_can_teach],
            'courses_can_teach_names': [c.name for c in self.courses_can_teach],
            'available_slots': self.get_available_slots(),
            'photo_url': self.photo_url or ''
        }


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_uid = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=True, unique=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    photo_url = db.Column(db.Text, nullable=True)
    courses_enrolled = db.relationship('Course', secondary=student_courses, lazy='subquery',
                                        backref=db.backref('enrolled_students', lazy=True))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        if not self.password_hash: return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'student_uid': self.student_uid,
            'name': self.name,
            'email': self.email or '',
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else '',
            'courses_enrolled': [c.id for c in self.courses_enrolled],
            'courses_enrolled_names': [c.name for c in self.courses_enrolled],
            'photo': self.photo_url or ''
        }


class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=False)  # A, B, C...
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    student_count = db.Column(db.Integer, default=0)
    students = db.relationship('Student', secondary=section_students, lazy='subquery',
                                backref=db.backref('sections', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else '',
            'department_code': self.department.code if self.department else '',
            'student_count': self.student_count,
            'student_ids': [s.id for s in self.students]
        }


class Classroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    block = db.Column(db.Integer, nullable=False)
    floor = db.Column(db.Integer, nullable=False, default=1)
    room_number = db.Column(db.String(20), nullable=False)
    capacity = db.Column(db.Integer, default=60)
    room_type = db.Column(db.String(20), default='Theory')  # Theory, Lab

    def to_dict(self):
        return {
            'id': self.id,
            'block': self.block,
            'floor': self.floor,
            'room_number': self.room_number,
            'capacity': self.capacity,
            'room_type': self.room_type
        }


class TimetableEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    day = db.Column(db.String(20), nullable=False)
    timeslot = db.Column(db.String(20), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id'), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False)

    section = db.relationship('Section', backref='timetable_entries')
    course = db.relationship('Course', backref='timetable_entries')
    faculty = db.relationship('Faculty', backref='timetable_entries')
    classroom = db.relationship('Classroom', backref='timetable_entries')

    def to_dict(self):
        return {
            'id': self.id,
            'section_id': self.section_id,
            'section_name': f"{self.section.department.code}-{self.section.name}" if self.section else '',
            'day': self.day,
            'timeslot': self.timeslot,
            'course_id': self.course_id,
            'course_name': self.course.name if self.course else '',
            'course_code': self.course.code if self.course else '',
            'faculty_id': self.faculty_id,
            'faculty_name': self.faculty.name if self.faculty else '',
            'classroom_id': self.classroom_id,
            'room_number': self.classroom.room_number if self.classroom else '',
            'block': self.classroom.block if self.classroom else ''
        }


class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), nullable=False)
    otp_hash = db.Column(db.String(255), nullable=False)
    reset_token = db.Column(db.String(100), nullable=True, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)

    def set_otp(self, otp):
        self.otp_hash = generate_password_hash(str(otp), method='pbkdf2:sha256')

    def check_otp(self, otp):
        return check_password_hash(self.otp_hash, str(otp))

    def is_expired(self):
        return datetime.utcnow() > self.expires_at


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(10), nullable=False, default='absent')  # 'present' or 'absent'

    student = db.relationship('Student', backref='attendance_records')
    course = db.relationship('Course', backref='attendance_records')
    section = db.relationship('Section', backref='attendance_records')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'course_id': self.course_id,
            'section_id': self.section_id,
            'date': self.date.isoformat() if self.date else '',
            'status': self.status
        }


class FacultyAbsence(db.Model):
    __tablename__ = 'faculty_absence'
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    slots = db.Column(db.Text, nullable=False)  # JSON list of slots: ["9-10", "10-11"]
    reason = db.Column(db.String(255), nullable=True)

    faculty = db.relationship('Faculty', backref='absences')

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_id': self.faculty_id,
            'faculty_uid': self.faculty.faculty_uid if self.faculty else '',
            'faculty_email': self.faculty.email if self.faculty else '',
            'day': self.date.isoformat() if self.date else '',
            'date': self.date.isoformat() if self.date else '',
            'slots': json.loads(self.slots) if self.slots else [],
            'reason': self.reason
        }


class Complaint(db.Model):
    __tablename__ = 'complaint'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)

    priority = db.Column(db.String(20), default='medium')

    submitted_by_role = db.Column(db.String(20), nullable=False)
    submitted_by_id = db.Column(db.Integer, nullable=False)
    submitted_by_name = db.Column(db.String(100), nullable=False)
    submitted_by_email = db.Column(db.String(150), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    department_name = db.Column(db.String(100), nullable=True)

    assigned_to = db.Column(db.String(100), nullable=True)
    assigned_to_role = db.Column(db.String(50), nullable=True)

    status = db.Column(db.String(20), default='open')

    is_anonymous = db.Column(db.Boolean, default=False)
    is_urgent = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    resolution_note = db.Column(db.Text, nullable=True)
    admin_remarks = db.Column(db.Text, nullable=True)

    def generate_ticket_id(self):
        year = datetime.utcnow().year
        self.ticket_id = f"CMP-{year}-{self.id:04d}"

    def to_dict(self):
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'priority': self.priority,
            'submitted_by_role': self.submitted_by_role,
            'submitted_by_name': 'Anonymous' if self.is_anonymous else self.submitted_by_name,
            'submitted_by_email': '' if self.is_anonymous else self.submitted_by_email,
            'department_name': self.department_name,
            'assigned_to': self.assigned_to,
            'assigned_to_role': self.assigned_to_role,
            'status': self.status,
            'is_anonymous': self.is_anonymous,
            'is_urgent': self.is_urgent,
            'created_at': self.created_at.isoformat() if self.created_at else '',
            'updated_at': self.updated_at.isoformat() if self.updated_at else '',
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolution_note': self.resolution_note,
            'admin_remarks': self.admin_remarks,
        }
