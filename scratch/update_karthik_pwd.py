import sys
import os
sys.path.append(os.getcwd())
from app import app
from models import db, Student
from werkzeug.security import generate_password_hash

with app.app_context():
    s = Student.query.filter_by(student_uid='STU0001').first()
    if s:
        s.password_hash = generate_password_hash('karthik@123', method='pbkdf2:sha256')
        db.session.commit()
        print("Password updated for Karthik Reddi")
    else:
        print("Student STU0001 not found")
