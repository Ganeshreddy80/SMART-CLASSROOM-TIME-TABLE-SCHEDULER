from app import app, db
from models import TimetableEntry
from timetable_generator import generate_timetable

with app.app_context():
    print('Before:', TimetableEntry.query.count())
    res = generate_timetable()
    print('Result:', res['entries_created'], 'Conflicts:', len(res.get('conflicts', [])))
    for c in res.get('conflicts', []):
        print(c)
