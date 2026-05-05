import re
from app import app, db
from models import Faculty, Student

def get_first_name(name):
    # Remove titles
    cleaned = re.sub(r'^(Dr\.?|Prof\.?|Mr\.?|Mrs\.?|Ms\.?)\s+', '', name.strip(), flags=re.IGNORECASE)
    parts = cleaned.strip().split()
    return parts[0] if parts else 'User'

with app.app_context():
    print("Resetting all Faculty passwords...")
    faculties = Faculty.query.all()
    for f in faculties:
        fname = get_first_name(f.name)
        new_pass = f"{fname}#SRM2026"
        f.set_password(new_pass)
        print(f"  - {f.name}: {new_pass}")
    
    print("\nResetting all Student passwords...")
    students = Student.query.all()
    for s in students:
        fname = get_first_name(s.name)
        new_pass = f"{fname}#SRM2026"
        s.set_password(new_pass)
        if s.student_uid == 'STU0001': # Karthik
            print(f"  - {s.name}: {new_pass} (STU0001)")
    
    db.session.commit()
    print("\nAll passwords reset successfully to [FirstName]#SRM2026 pattern.")
