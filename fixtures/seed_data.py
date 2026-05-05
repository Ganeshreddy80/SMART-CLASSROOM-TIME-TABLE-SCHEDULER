"""
Seed script — populates the university timetable system with large realistic data.

Usage:
    1. Start the Flask server:  python3 app.py
    2. In another terminal:     python3 fixtures/seed_data.py

The script uses the running Flask API to seed the database, so the server must
be running first.  It also imports `app` and `db` directly to clear existing
data before seeding.
"""
import sys, os

# Allow imports from the project root (one level up)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests, random

BASE = "http://127.0.0.1:5001/api"

req_session = requests.Session()
req_session.post("http://127.0.0.1:5001/login", data={"email": "admin@srmap.edu.in", "password": os.getenv("ADMIN_PASSWORD", "sukuna@123")})

# ── 0. Clear existing data ───────────────────────────────────
print("🗑️  Clearing existing data...")
from app import app, db
from models import TimetableEntry, Section, Student, Faculty, Course, Department, Classroom, University
from models import section_students, student_courses, faculty_courses
with app.app_context():
    db.create_all()
    db.session.execute(TimetableEntry.__table__.delete())
    db.session.execute(section_students.delete())
    db.session.execute(student_courses.delete())
    db.session.execute(faculty_courses.delete())
    db.session.execute(Section.__table__.delete())
    db.session.execute(Student.__table__.delete())
    db.session.execute(Faculty.__table__.delete())
    db.session.execute(Course.__table__.delete())
    db.session.execute(Department.__table__.delete())
    db.session.execute(Classroom.__table__.delete())
    db.session.execute(University.__table__.delete())
    db.session.commit()
print("   ✓ Database cleared")
# ── 1. University Setup ──────────────────────────────────────
print("🏛️  Setting up university...")
req_session.post(f"{BASE}/university", json={
    "name": "SRM University AP",
    "total_blocks": 4,
    "floors_per_block": {"1": 3, "2": 4, "3": 2, "4": 3},
    "rooms_per_block": 5,
    "room_capacity": 60,
    "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "timeslots": [
        "9:00-10:00", "10:00-11:00", "11:00-12:00",
        "12:00-1:00", "2:00-3:00", "3:00-4:00", "4:00-5:00"
    ]
})
print("   ✓ University configured (4 blocks, 60 classrooms)")

# ── 2. Departments ───────────────────────────────────────────
print("🏢  Creating departments...")
departments = [
    ("Computer Science", "CSE"),
    ("Electronics", "ECE"),
    ("Mechanical", "MECH"),
    ("Civil", "CIVIL"),
    ("Information Technology", "IT"),
    ("Artificial Intelligence", "AI"),
]
dept_ids = {}
for name, code in departments:
    r = req_session.post(f"{BASE}/departments", json={"name": name, "code": code}).json()
    dept_ids[code] = r.get("id", len(dept_ids) + 1)
print(f"   ✓ {len(departments)} departments created")

# Re-fetch to get correct IDs
depts = req_session.get(f"{BASE}/departments").json()
dept_ids = {d["code"]: d["id"] for d in depts}

# ── 3. Courses ───────────────────────────────────────────────
print("📖  Creating courses...")
course_defs = {
    "CSE": [
        ("CS101", "Data Structures", 4, "Hard", "Theory"),
        ("CS102", "Algorithms", 4, "Hard", "Theory"),
        ("CS103", "Database Systems", 3, "Medium", "Theory"),
        ("CS104", "Operating Systems", 4, "Hard", "Theory"),
        ("CS105", "Computer Networks", 3, "Medium", "Theory"),
        ("CS106", "Web Development", 3, "Easy", "Lab"),
        ("CS107", "Machine Learning", 4, "Hard", "Theory"),
        ("CS108", "Software Engineering", 3, "Medium", "Theory"),
    ],
    "ECE": [
        ("EC101", "Circuit Analysis", 4, "Hard", "Theory"),
        ("EC102", "Signal Processing", 4, "Hard", "Theory"),
        ("EC103", "Electromagnetics", 3, "Medium", "Theory"),
        ("EC104", "VLSI Design", 4, "Hard", "Lab"),
        ("EC105", "Communication Systems", 3, "Medium", "Theory"),
        ("EC106", "Embedded Systems", 3, "Medium", "Lab"),
    ],
    "MECH": [
        ("ME101", "Thermodynamics", 4, "Hard", "Theory"),
        ("ME102", "Fluid Mechanics", 4, "Hard", "Theory"),
        ("ME103", "Strength of Materials", 3, "Medium", "Theory"),
        ("ME104", "Manufacturing Processes", 3, "Medium", "Lab"),
        ("ME105", "CAD/CAM", 3, "Easy", "Lab"),
        ("ME106", "Heat Transfer", 4, "Hard", "Theory"),
    ],
    "CIVIL": [
        ("CE101", "Structural Analysis", 4, "Hard", "Theory"),
        ("CE102", "Geotechnical Engineering", 3, "Medium", "Theory"),
        ("CE103", "Surveying", 3, "Easy", "Lab"),
        ("CE104", "Concrete Technology", 3, "Medium", "Theory"),
        ("CE105", "Transportation Engineering", 3, "Medium", "Theory"),
    ],
    "IT": [
        ("IT101", "Cloud Computing", 3, "Medium", "Theory"),
        ("IT102", "Cybersecurity", 4, "Hard", "Theory"),
        ("IT103", "DevOps", 3, "Medium", "Lab"),
        ("IT104", "Big Data Analytics", 4, "Hard", "Theory"),
        ("IT105", "Mobile App Development", 3, "Easy", "Lab"),
    ],
    "AI": [
        ("AI101", "Deep Learning", 4, "Hard", "Theory"),
        ("AI102", "Natural Language Processing", 4, "Hard", "Theory"),
        ("AI103", "Computer Vision", 3, "Medium", "Theory"),
        ("AI104", "Reinforcement Learning", 4, "Hard", "Theory"),
        ("AI105", "AI Ethics", 2, "Easy", "Theory"),
        ("AI106", "Neural Networks Lab", 3, "Medium", "Lab"),
    ],
}

course_ids = {}
total_courses = 0
for dept_code, courses in course_defs.items():
    for code, name, credits, diff, ctype in courses:
        r = req_session.post(f"{BASE}/courses", json={
            "code": code, "name": name, "credits": credits,
            "difficulty": diff, "course_type": ctype,
            "department_id": dept_ids[dept_code]
        }).json()
        course_ids[code] = r.get("id", total_courses + 1)
        total_courses += 1
print(f"   ✓ {total_courses} courses created")

# Re-fetch course IDs
courses_all = req_session.get(f"{BASE}/courses").json()
course_ids = {c["code"]: c["id"] for c in courses_all}
courses_by_dept = {}
for c in courses_all:
    courses_by_dept.setdefault(c["department_id"], []).append(c)

# Get university timeslots for faculty availability
uni = req_session.get(f"{BASE}/university").json()
timeslots = uni.get("timeslots", [])

# ── 4. Faculty ───────────────────────────────────────────────
print("👨‍🏫  Creating faculty...")
faculty_defs = {
    "CSE": [
        ("FAC001", "Dr. Rajesh Kumar", ["CS101", "CS102"]),
        ("FAC002", "Prof. Anita Sharma", ["CS103", "CS108"]),
        ("FAC003", "Dr. Vikram Patel", ["CS104", "CS105"]),
        ("FAC004", "Prof. Meera Reddy", ["CS106", "CS107"]),
    ],
    "ECE": [
        ("FAC005", "Dr. Suresh Babu", ["EC101", "EC102"]),
        ("FAC006", "Prof. Lakshmi Devi", ["EC103", "EC105"]),
        ("FAC007", "Dr. Arjun Rao", ["EC104", "EC106"]),
    ],
    "MECH": [
        ("FAC008", "Dr. Prakash Joshi", ["ME101", "ME102"]),
        ("FAC009", "Prof. Kavitha Nair", ["ME103", "ME106"]),
        ("FAC010", "Dr. Raman Singh", ["ME104", "ME105"]),
    ],
    "CIVIL": [
        ("FAC011", "Dr. Sunita Patel", ["CE101", "CE102"]),
        ("FAC012", "Prof. Arun Kumar", ["CE103", "CE104", "CE105"]),
    ],
    "IT": [
        ("FAC013", "Dr. Deepa Menon", ["IT101", "IT102"]),
        ("FAC014", "Prof. Karthik Iyer", ["IT103", "IT104", "IT105"]),
    ],
    "AI": [
        ("FAC015", "Dr. Priya Krishnan", ["AI101", "AI102"]),
        ("FAC016", "Prof. Sanjay Gupta", ["AI103", "AI104"]),
        ("FAC017", "Dr. Nisha Verma", ["AI105", "AI106"]),
    ],
}

total_faculty = 0
days_list = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
for dept_code, facs in faculty_defs.items():
    for uid, name, course_codes in facs:
        cids = [course_ids[c] for c in course_codes if c in course_ids]
        # Build per-day availability map
        avail = {day: timeslots for day in days_list}
        r = req_session.post(f"{BASE}/faculty", json={
            "faculty_uid": uid,
            "name": name,
            "department_id": dept_ids[dept_code],
            "courses_can_teach": cids,
            "available_slots": avail
        })
        total_faculty += 1
print(f"   ✓ {total_faculty} faculty members created")

# ── 5. Students ──────────────────────────────────────────────
print("🎓  Enrolling students...")
first_names = ["Aarav", "Aditi", "Arjun", "Diya", "Ishaan", "Kavya", "Rohan", "Priya", 
               "Vivaan", "Ananya", "Siddharth", "Neha", "Aditya", "Pooja", "Rahul",
               "Shreya", "Vihaan", "Riya", "Karan", "Sakshi", "Dev", "Tanvi", "Nikhil",
               "Anjali", "Manish", "Divya", "Akash", "Simran", "Varun", "Meghna",
               "Harsh", "Kritika", "Rajat", "Swati", "Pranav", "Nandini", "Gaurav",
               "Isha", "Kunal", "Tanya"]
last_names = ["Sharma", "Patel", "Kumar", "Singh", "Reddy", "Gupta", "Nair", "Iyer",
              "Joshi", "Verma", "Chauhan", "Mehta", "Rao", "Das", "Bhat", "Malhotra",
              "Pillai", "Mishra", "Saxena", "Agarwal"]

total_students = 0
stu_counter = 1
for dept_code, did in dept_ids.items():
    dept_courses = courses_by_dept.get(did, [])
    num_students = random.randint(45, 80)
    
    for i in range(num_students):
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        # Each student enrolls in 4-6 courses from their department
        num_enroll = min(len(dept_courses), random.randint(4, 6))
        enrolled = random.sample([c["id"] for c in dept_courses], num_enroll)
        
        req_session.post(f"{BASE}/students", json={
            "student_uid": f"STU{stu_counter:04d}",
            "name": f"{fname} {lname}",
            "department_id": did,
            "courses_enrolled": enrolled
        })
        stu_counter += 1
        total_students += 1

print(f"   ✓ {total_students} students enrolled")

# ── 6. Generate Sections ─────────────────────────────────────
print("👥  Generating sections...")
r = req_session.post(f"{BASE}/sections/generate").json()
print(f"   ✓ {r.get('message', 'Sections generated')}")

# ── 7. Generate Timetable ────────────────────────────────────
print("⚡  Generating timetable...")
r = req_session.post(f"{BASE}/timetable/generate").json()
print(f"   ✓ {r.get('message', 'Done')}")
if r.get("conflicts"):
    print(f"   ⚠ {len(r['conflicts'])} conflicts detected")

# ── Summary ──────────────────────────────────────────────────
print("\n" + "="*50)
dash = req_session.get(f"{BASE}/dashboard").json()
print(f"📊 DASHBOARD SUMMARY")
print(f"   Departments:      {dash.get('departments', 0)}")
print(f"   Courses:          {dash.get('courses', 0)}")
print(f"   Faculty:          {dash.get('faculty', 0)}")
print(f"   Students:         {dash.get('students', 0)}")
print(f"   Sections:         {dash.get('sections', 0)}")
print(f"   Timetable Slots:  {dash.get('timetable_entries', 0)}")
print("="*50)
print("✅ Seed complete! Open http://127.0.0.1:5001 to view.")
