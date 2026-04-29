
import sys, os
sys.path.append(os.getcwd())
from app import app
from models import db, TimetableEntry

with app.app_context():
    count = TimetableEntry.query.filter_by(timeslot="12:00-1:00").count()
    print(f"Entries in 12:00-1:00 slot: {count}")
    
    # Also check max classes per day
    from sqlalchemy import func
    rows = db.session.query(
        TimetableEntry.section_id, TimetableEntry.day, func.count(TimetableEntry.id)
    ).group_by(TimetableEntry.section_id, TimetableEntry.day).all()
    max_classes = max([r[2] for r in rows]) if rows else 0
    print(f"Max classes in any day for any section: {max_classes}")
