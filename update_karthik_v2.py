from app import app, db
from models import Student

with app.app_context():
    s = Student.query.filter_by(student_uid='STU0001').first()
    if s:
        s.photo_url = "/static/uploads/students/karthik.png"
        db.session.commit()
        print(f"Successfully updated photo for {s.name}")
    else:
        print("Student STU0001 not found.")
