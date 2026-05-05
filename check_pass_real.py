from app import app, db
from models import Faculty, Student, generate_default_password

with app.app_context():
    faculty = Faculty.query.first()
    student = Student.query.first()
    
    f_pass = generate_default_password(faculty.name)
    s_pass = generate_default_password(student.name)
    
    print(f"Faculty: {faculty.email} | Password: {f_pass} | Check: {faculty.check_password(f_pass)}")
    print(f"Student: {student.email} | Password: {s_pass} | Check: {student.check_password(s_pass)}")
