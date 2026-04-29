from app import app, db
from models import Student

with app.app_context():
    s = Student.query.filter_by(student_uid='STU0001').first()
    if s:
        new_pass = "Karthik#SRM2026"
        s.set_password(new_pass)
        db.session.commit()
        print(f"Password for {s.name} reset to: {new_pass}")
        print(f"Verification: {s.check_password(new_pass)}")
    else:
        print("Karthik not found")
