from app import app, db
from models import Faculty

PHOTO_MAP = {
    'FAC001': '/static/uploads/faculty/yasir.png',
    'FAC002': '/static/uploads/faculty/anita.png',
    'FAC003': '/static/uploads/faculty/vikram.png',
    'FAC004': '/static/uploads/faculty/meera.png',
    'FAC005': '/static/uploads/faculty/suresh.png',
    'FAC006': '/static/uploads/faculty/lakshmi.png',
    'FAC007': '/static/uploads/faculty/arjun.png',
    'FAC008': '/static/uploads/faculty/prakash.png',
    'FAC009': '/static/uploads/faculty/kavitha.png',
    'FAC010': '/static/uploads/faculty/raman.png',
    'FAC011': '/static/uploads/faculty/sunita.png',
    'FAC012': '/static/uploads/faculty/arun.png',
    'FAC013': '/static/uploads/faculty/deepa.png',
    'FAC014': '/static/uploads/faculty/karthik.png',
    'FAC015': '/static/uploads/faculty/priya.png',
    'FAC016': '/static/uploads/faculty/sanjay.png',
    'FAC017': '/static/uploads/faculty/nisha.png',
}

with app.app_context():
    for uid, url in PHOTO_MAP.items():
        f = Faculty.query.filter_by(faculty_uid=uid).first()
        if f:
            f.photo_url = url
            print(f"Updated {f.name} -> {url}")
        else:
            print(f"Not found: {uid}")
    db.session.commit()
    print("All done!")
