from app import app, db
from models import Faculty

with app.app_context():
    faculties = Faculty.query.all()
    for f in faculties:
        f.set_password("password123")
    db.session.commit()
    print("All faculty passwords successfully reset to 'password123'")
