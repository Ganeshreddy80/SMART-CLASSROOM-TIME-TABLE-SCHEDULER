import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, db
from models import Section, Student, Faculty, Course

with app.app_context():
    print(f"Students: {Student.query.count()}")
    print(f"Sections: {Section.query.count()}")
    print(f"Courses: {Course.query.count()}")
    print(f"Faculty: {Faculty.query.count()}")
    for f in Faculty.query.all():
        print(f"Faculty {f.name}: teaches {len(f.courses_can_teach)} courses")
    for c in Course.query.all():
        print(f"Course {c.code}: has {len(c.faculty_members)} faculty")
