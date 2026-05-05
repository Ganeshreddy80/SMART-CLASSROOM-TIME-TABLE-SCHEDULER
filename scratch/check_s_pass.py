from app import app, db
from models import Student
with app.app_context():
    s = Student.query.filter_by(email='gaurav.gupta1@srmap.edu.in').first()
    print(f"Testing 'gaurav@123': {s.check_password('gaurav@123')}")
    print(f"Testing 'Gaurav@123': {s.check_password('Gaurav@123')}")
    print(f"Testing 'SRM@2024': {s.check_password('SRM@2024')}")
