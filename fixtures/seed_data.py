"""
Seed script — populates the university timetable system with minimal seed data.
"""
import sys, os, json
from werkzeug.security import generate_password_hash

# Allow imports from the project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app, db
from models import (
    University, Department, Course, Faculty, Student, Section, Classroom, TimetableEntry
)

def _seed():
    with app.app_context():
        print("Force reseeding database...")
            
        print("🗑️ Clearing existing data...")
        db.session.query(TimetableEntry).delete()
        db.session.query(Classroom).delete()
        db.session.query(Section).delete()
        db.session.query(Student).delete()
        db.session.query(Faculty).delete()
        db.session.query(Course).delete()
        db.session.query(Department).delete()
        db.session.query(University).delete()
        db.session.commit()

        print("🏛️ Creating basic seed data...")
        
        uni = University(
            name="SRM University AP",
            total_blocks=1,
            floors_per_block=json.dumps({"1": 1}),
            rooms_per_block=1,
            room_capacity=60,
            days=json.dumps(["Monday"]),
            timeslots=json.dumps(["9:00-10:00"])
        )
        db.session.add(uni)
        db.session.flush()
        
        dept = Department(name="Computer Science", code="CSE", university_id=uni.id)
        db.session.add(dept)
        db.session.flush()
        
        course = Course(code="CS101", name="Data Structures", credits=4, department_id=dept.id)
        db.session.add(course)
        db.session.flush()
        
        faculty = Faculty(
            faculty_uid="FAC001",
            name="Dr. Rajesh Kumar",
            email="rajesh.k@srmap.edu.in",
            department_id=dept.id,
            password_hash=generate_password_hash('password123')
        )
        faculty.courses_can_teach.append(course)
        db.session.add(faculty)
        
        student = Student(
            student_uid="STU0001",
            name="Aarav Sharma",
            email="aarav.s@srmap.edu.in",
            department_id=dept.id,
            password_hash=generate_password_hash('password123')
        )
        student.courses_enrolled.append(course)
        db.session.add(student)
        db.session.flush()
        
        section = Section(name="A", department_id=dept.id, student_count=1)
        section.students.append(student)
        db.session.add(section)
        db.session.flush()
        
        classroom = Classroom(block=1, floor=1, room_number="101", capacity=60)
        db.session.add(classroom)
        db.session.flush()
        
        timetable_entry = TimetableEntry(
            section_id=section.id,
            day="Monday",
            timeslot="9:00-10:00",
            course_id=course.id,
            faculty_id=faculty.id,
            classroom_id=classroom.id
        )
        db.session.add(timetable_entry)
        db.session.commit()
        
        print("✅ Basic seed data created successfully!")

if __name__ == "__main__":
    try:
        _seed()
    except Exception as e:
        print(f"Seed failed: {e}")

