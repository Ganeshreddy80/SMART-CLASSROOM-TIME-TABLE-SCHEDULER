from app import app
from models import Faculty

with app.app_context():
    for f in Faculty.query.limit(5).all():
        print(f"Name: {f.name} | Email: {f.email} | Default Password: {f.email.split('@')[0].split('.')[0]}#SRM2026")
