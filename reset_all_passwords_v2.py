import re
from app import app, db
from models import Faculty, Student

def get_first_name(name):
    cleaned = re.sub(r'^(Dr\.?|Prof\.?|Mr\.?|Mrs\.?|Ms\.?)\s+', '', name.strip(), flags=re.IGNORECASE)
    parts = cleaned.strip().split()
    return parts[0] if parts else 'User'

with app.app_context():
    print("Resetting all Faculty passwords...")
    faculties = Faculty.query.all()
    for i, f in enumerate(faculties):
        fname = get_first_name(f.name)
        new_pass = f"{fname}#SRM2026"
        f.set_password(new_pass)
        if i % 10 == 0:
            db.session.commit()
            print(f"  Processed {i} faculties...")
    db.session.commit()
    
    print("\nResetting all Student passwords...")
    students = Student.query.all()
    for i, s in enumerate(students):
        fname = get_first_name(s.name)
        new_pass = f"{fname}#SRM2026"
        s.set_password(new_pass)
        if i % 50 == 0:
            db.session.commit()
            print(f"  Processed {i} students...")
    db.session.commit()
    print("\nAll passwords reset successfully.")
