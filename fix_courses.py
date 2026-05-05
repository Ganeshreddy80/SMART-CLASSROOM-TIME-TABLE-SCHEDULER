from app import app, db
from models import Course
from blueprints.utils import calc_classes_per_week

with app.app_context():
    courses = Course.query.all()
    for c in courses:
        c.classes_per_week = calc_classes_per_week(c.difficulty, c.credits)
    db.session.commit()
    print("Fixed classes_per_week for all courses.")
