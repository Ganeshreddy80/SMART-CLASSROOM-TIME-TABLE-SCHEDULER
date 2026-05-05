from app import app, db
from models import Faculty

with app.app_context():
    f = Faculty.query.filter_by(faculty_uid='FAC001').first()
    if f:
        f.photo_url = '/static/uploads/faculty/yasir.png'
        db.session.commit()
        print("Updated Yasir Afaq photo_url")
    else:
        print("Could not find FAC001")
