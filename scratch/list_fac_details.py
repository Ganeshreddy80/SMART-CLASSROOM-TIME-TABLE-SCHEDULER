import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from models import Faculty

with app.app_context():
    facs = Faculty.query.limit(5).all()
    for f in facs:
        first_name = f.name.split()[1].lower() if 'Dr.' in f.name or 'Prof.' in f.name else f.name.split()[0].lower()
        # Wait, the default password generator in models.py might be different.
        # Let's check models.py
        print(f"Name: {f.name} | Email: {f.email}")
