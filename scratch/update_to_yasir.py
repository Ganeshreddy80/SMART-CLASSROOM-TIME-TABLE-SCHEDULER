import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app import app, db
from models import Faculty
import os
from werkzeug.security import generate_password_hash

with app.app_context():
    f = Faculty.query.filter_by(faculty_uid='FAC001').first()
    if f:
        f.name = "Yasir Afaq"
        f.email = "yasir.afaq@srmap.edu.in"
        f.photo_url = "/static/uploads/faculty/yasir.png"
        f.password_hash = generate_password_hash("yasir@123", method='pbkdf2:sha256')
        db.session.commit()
        print("Updated FAC001 to Yasir Afaq")
    else:
        print("FAC001 not found")
