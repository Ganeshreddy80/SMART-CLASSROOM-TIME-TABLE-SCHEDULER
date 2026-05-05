import pytest
from timetable_generator import generate_timetable, validate_timetable
from models import db, Classroom, Course, Faculty, Section, University
import json

def test_basic_generation(app, seed_minimal):
    with app.app_context():
        res = generate_timetable()
        assert res['success'] is True
        assert res['entries_created'] == 4  # 2 courses * 2 classes per week
        assert len(res['conflicts']) == 0

def test_no_classrooms(app, seed_minimal):
    with app.app_context():
        Classroom.query.delete()
        db.session.commit()
        
        res = generate_timetable()
        assert res['success'] is False
        assert 'No classrooms found' in res['message']

def test_faculty_conflict(app, seed_minimal):
    with app.app_context():
        # Add another section that also needs the same faculty
        d = Section.query.first().department
        sec2 = Section(name="B", department_id=d.id, student_count=1)
        db.session.add(sec2)
        db.session.commit()
        
        # Generation should try to place classes for both sections
        generate_timetable()
        
        # Validate that the same faculty isn't double booked
        val = validate_timetable()
        assert val['valid'] is True, f"Violations found: {val['violations']}"

def test_room_conflict(app, seed_minimal):
    with app.app_context():
        # Delete one classroom so only 1 exists
        Classroom.query.filter_by(room_number="R2").delete()
        db.session.commit()
        
        generate_timetable()
        
        val = validate_timetable()
        assert val['valid'] is True
        
        room_violations = [v for v in val['violations'] if v['type'] == 'room_double_booked']
        assert len(room_violations) == 0

def test_max_classes_per_day(app, seed_minimal):
    with app.app_context():
        # Add a 3rd course to exceed slots
        d = Section.query.first().department
        c3 = Course(code="CS103", name="Extra", department_id=d.id, credits=3, difficulty="Medium", classes_per_week=3, course_type="Theory")
        db.session.add(c3)
        
        f = Faculty.query.first()
        f.courses_can_teach.append(c3)
        db.session.commit()
        
        generate_timetable()
        
        val = validate_timetable()
        assert val['valid'] is True
        
        sec_violations = [v for v in val['violations'] if v['type'] == 'section_over_scheduled']
        assert len(sec_violations) == 0

def test_conflict_report(app, seed_minimal):
    with app.app_context():
        # Create an impossible scenario: 10 courses, only 2 slots available
        d = Section.query.first().department
        f = Faculty.query.first()
        for i in range(10):
            c = Course(code=f"IMP{i}", name=f"Impossible {i}", department_id=d.id, credits=2, difficulty="Easy", classes_per_week=2, course_type="Theory")
            db.session.add(c)
            f.courses_can_teach.append(c)
        db.session.commit()
        
        res = generate_timetable()
        assert res['success'] is True
        assert len(res['conflicts']) > 0
        
        # Check that the conflict has structured reasons
        first_conflict = res['conflicts'][0]
        assert 'course_code' in first_conflict
        assert 'reason' in first_conflict
        assert first_conflict['reason'] == 'partially_scheduled'
        assert 'reasons' in first_conflict
        assert 'section_full' in first_conflict['reasons']
