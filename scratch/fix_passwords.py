
import sys, os
sys.path.append(os.getcwd())
from app import app
from models import Faculty, Student, generate_default_password, db

with app.app_context():
    print("--- DEBUGGING LOGIN ---")
    f = Faculty.query.filter_by(email='rajesh.kumar@srmap.edu.in').first()
    if f:
        pwd = generate_default_password(f.name)
        match = f.check_password(pwd)
        print(f"Faculty: {f.name} | Email: {f.email}")
        print(f"Calculated Pwd: {pwd}")
        print(f"Hash Match: {match}")
        if not match:
            print("Resetting password for Rajesh...")
            f.set_password(pwd)
            db.session.commit()
            print("Password reset successfully.")
            
    s = Student.query.filter_by(email='gaurav.gupta1@srmap.edu.in').first()
    if s:
        pwd = generate_default_password(s.name)
        match = s.check_password(pwd)
        print(f"\nStudent: {s.name} | Email: {s.email}")
        print(f"Calculated Pwd: {pwd}")
        print(f"Hash Match: {match}")
        if not match:
            print("Resetting password for Gaurav...")
            s.set_password(pwd)
            db.session.commit()
            print("Password reset successfully.")
