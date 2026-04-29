import pytest
import os
import json
from app import app as flask_app
from models import db, University, Department, Course, Faculty, Student, Section, Classroom

@pytest.fixture
def app():
    # Setup in-memory SQLite database
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing simplicity
    
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def seed_minimal(app):
    """Seed minimal data required for testing generation."""
    with app.app_context():
        u = University(
            name="Test Uni",
            total_blocks=1,
            floors_per_block='{"1": 1}',
            rooms_per_block=2,
            room_capacity=60,
            days=json.dumps(["Monday", "Tuesday"]),
            timeslots=json.dumps(["9:00-10:00", "10:00-11:00"])
        )
        db.session.add(u)
        
        d = Department(name="Computer Science", code="CSE")
        db.session.add(d)
        db.session.commit()
        
        c1 = Course(code="CS101", name="Intro", department_id=d.id, credits=2, difficulty="Easy", classes_per_week=2, course_type="Theory")
        c2 = Course(code="CS102", name="Advanced", department_id=d.id, credits=2, difficulty="Hard", classes_per_week=2, course_type="Theory")
        db.session.add_all([c1, c2])
        db.session.commit()
        
        f = Faculty(
            faculty_uid="FAC1",
            name="Test Faculty",
            email="test.faculty@srmap.edu.in",
            department_id=d.id,
            available_slots=json.dumps({"Monday": ["9:00-10:00", "10:00-11:00"], "Tuesday": ["9:00-10:00", "10:00-11:00"]})
        )
        f.set_password("faculty@123")
        f.courses_can_teach = [c1, c2]
        db.session.add(f)
        
        s = Student(
            student_uid="STU1",
            name="Test Student",
            email="test.student@srmap.edu.in",
            department_id=d.id
        )
        s.set_password("student@123")
        s.courses_enrolled = [c1, c2]
        db.session.add(s)
        
        sec = Section(name="A", department_id=d.id, student_count=1)
        sec.students = [s]
        db.session.add(sec)
        
        cr1 = Classroom(block=1, floor=1, room_number="R1", capacity=60, room_type="Theory")
        cr2 = Classroom(block=1, floor=1, room_number="R2", capacity=60, room_type="Theory")
        db.session.add_all([cr1, cr2])
        db.session.commit()

@pytest.fixture
def admin_session(client):
    """Log in as admin."""
    # Assuming ADMIN_PASSWORD is set in environment since app starts.
    password = os.getenv('ADMIN_PASSWORD', 'sukuna@123')
    client.post('/login', data={'email': 'admin@srmap.edu.in', 'password': password})
    return client
