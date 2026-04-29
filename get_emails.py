from app import app, db
from models import Faculty, Student

with app.app_context():
    faculty = Faculty.query.first()
    student = Student.query.first()
    print(f"Faculty: {faculty.email}")
    print(f"Student: {student.email}")
