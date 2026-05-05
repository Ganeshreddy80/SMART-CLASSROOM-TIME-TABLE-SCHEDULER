from app import app
from models import Faculty

with app.app_context():
    for f in Faculty.query.all():
        print(f.id, f.faculty_uid, f.name)
