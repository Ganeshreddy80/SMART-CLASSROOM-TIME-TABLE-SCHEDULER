import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from models import Faculty, Student

email = "yasir.afaq@srmap.edu.in"

with app.app_context():
    f = Faculty.query.filter_by(email=email).first()
    if f:
        print(f"Found Faculty: {f.name}")
        print(f"ID: {f.id}")
        print(f"Role: faculty")
    else:
        s = Student.query.filter_by(email=email).first()
        if s:
            print(f"Found Student: {s.name}")
            print(f"ID: {s.id}")
            print(f"Role: student")
        else:
            print("User not found in current database.")
