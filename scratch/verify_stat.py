
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app import app, db
from models import Department, Section, Course, TimetableEntry

with app.app_context():
    total_entries = 0
    depts = Department.query.all()
    for d in depts:
        sections_in_dept = Section.query.filter_by(department_id=d.id).count()
        courses_in_dept = Course.query.filter_by(department_id=d.id).all()
        classes_sum = sum(c.classes_per_week for c in courses_in_dept)
        total_entries += (sections_in_dept * classes_sum)
    
    print(f"Calculated Timetable Entries: {total_entries}")
    print(f"Actual DB Timetable Entries: {TimetableEntry.query.count()}")
