from app import app, db
from models import Student

with app.app_context():
    s = Student.query.filter_by(student_uid='STU0001').first()
    if s:
        # Use the Base64 string that was previously provided or a high-quality path
        # Assuming the user wants the photo I previously set
        s.photo_url = "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=1974&auto=format&fit=crop"
        db.session.commit()
        print(f"Updated {s.name}'s photo.")
    else:
        print("Karthik Reddi (STU0001) not found.")
