import base64
import sys
import os

# Path to the NEW artifact
artifact_path = r"C:\Users\REDDI KARTHIK\.gemini\antigravity\brain\067fe2f9-3d86-4ce8-b25e-a2ef0dac2a53\.tempmediaStorage\media_067fe2f9-3d86-4ce8-b25e-a2ef0dac2a53_1776872892046.jpg"

try:
    with open(artifact_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode('utf-8')
        mime = "image/jpeg"
        data_url = f"data:{mime};base64,{b64}"
        
        # Now update the database
        sys.path.append(os.getcwd())
        from app import app
        from models import db, Student
        
        with app.app_context():
            s = Student.query.filter_by(student_uid='STU0001').first()
            if s:
                s.photo_url = data_url
                db.session.commit()
                print("SUCCESS: Photo updated with Base64 for the NEW image")
            else:
                print("ERROR: Student not found")
except Exception as e:
    print(f"ERROR: {str(e)}")
