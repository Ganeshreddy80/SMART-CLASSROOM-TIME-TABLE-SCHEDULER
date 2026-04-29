
import sys, os, re
sys.path.append(os.getcwd())
from app import app
from models import Faculty, Student, generate_default_password

with app.app_context():
    print("--- FACULTY EXAMPLES ---")
    facs = Faculty.query.limit(3).all()
    for f in facs:
        pwd = generate_default_password(f.name)
        print(f"Name: {f.name} | Email: {f.email} | Password: {pwd}")
        
    print("\n--- STUDENT EXAMPLES ---")
    stus = Student.query.limit(3).all()
    for s in stus:
        pwd = generate_default_password(s.name)
        print(f"Name: {s.name} | Email: {s.email} | Password: {pwd}")
