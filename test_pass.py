from app import app, db
from models import Faculty, Student

with app.app_context():
    faculty = Faculty.query.first()
    student = Student.query.first()
    
    print(f"Faculty: {faculty.email}, Name: {faculty.name}")
    print(f"Student: {student.email}, Name: {student.name}")
    
    f_first_name = faculty.name.split()[1] if faculty.name.startswith(('Dr.', 'Prof.')) else faculty.name.split()[0]
    expected_f_pass = f"{f_first_name}#SRM2026"
    print(f"Testing Faculty pass '{expected_f_pass}': {faculty.check_password(expected_f_pass)}")
    print(f"Testing Faculty pass 'faculty123': {faculty.check_password('faculty123')}")
    print(f"Testing Faculty pass 'arun.kumar@123': {faculty.check_password('arun.kumar@123')}")
    
    s_first_name = student.name.split()[0]
    expected_s_pass = f"{s_first_name}#SRM2026"
    print(f"Testing Student pass '{expected_s_pass}': {student.check_password(expected_s_pass)}")
    print(f"Testing Student pass 'student123': {student.check_password('student123')}")
