import sys
import os
sys.path.append(os.getcwd())
from app import app
from models import db, Student

with app.app_context():
    students = Student.query.all()
    print(f"Found {len(students)} students")
    for s in students:
        if s.student_uid == 'STU0001':
            s.photo_url = '/static/photos/STU0001.png'
        else:
            # Use a diverse set of avatars from a placeholder service
            # i.pravatar.cc is good because it gives unique photos for unique keys
            s.photo_url = f"https://i.pravatar.cc/150?u={s.student_uid}"
            
    db.session.commit()
    print("Photos updated for all students")
