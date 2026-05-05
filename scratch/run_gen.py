import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, db
from timetable_generator import generate_timetable

with app.app_context():
    print("🚀 Starting timetable generation...")
    result = generate_timetable()
    print(f"Result: {result['success']}")
    print(f"Message: {result['message']}")
    if not result['success']:
        print(f"Conflicts: {result.get('conflicts', [])}")
    else:
        print(f"Entries created: {result.get('entries_created', 0)}")
