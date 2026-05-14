"""
Seed script — populates the university timetable system with large realistic data.
Uses direct DB imports (no HTTP API), so it can be run during a Render deployment
before the app server starts.
"""
import sys, os, random, json

# Allow imports from the project root (one level up)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app, db
from models import (
    TimetableEntry, Section, Student, Faculty, Course, Department, Classroom, University,
    section_students, student_courses, faculty_courses,
)


def _seed():
    """Actual seeding logic."""

    # ── Guard: already seeded ───────────────────────────────────
    with app.app_context():
        if Department.query.count() > 0:
            print("Database already seeded, skipping!")
            return

    # ── 0. Clear existing data ─────────────────────────────────
    print("🗑️  Clearing existing data...")
    with app.app_context():
        for tbl in (
            TimetableEntry.__table__,
            section_students,
            student_courses,
            faculty_courses,
            Section.__table__,
            Student.__table__,
            Faculty.__table__,
            Course.__table__,
            Department.__table__,
            Classroom.__table__,
            University.__table__,
        ):
            db.session.execute(tbl.delete())
        db.session.commit()
    print("   ✓ Database cleared")

    # ── 1. University Setup ────────────────────────────────────
    print("🏛️  Setting up university...")
    with app.app_context():
        uni = University(
            name="SRM University AP",
            total_blocks=4,
            floors_per_block=json.dumps({"1": 3, "2": 4, "3": 2, "4": 3}),
            rooms_per_block=5,
            room_capacity=60,
            days=json.dumps(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]),
            timeslots=json.dumps([
                "9:00-10:00", "10:00-11:00", "11:00-12:00",
                "12:00-1:00", "2:00-3:00", "3:00-4:00", "4:00-5:00"
            ]),
        )
        db.session.add(uni)
        db.session.commit()
        uni_id = uni.id
    print("   ✓ University configured (4 blocks, 60 classrooms)")

    # ── 2. Departments ───────────────────────────────────────────
    print("🏢  Creating departments...")
    department_data = [
        ("Computer Science", "CSE"),
        ("Electronics", "ECE"),
        ("Mechanical", "MECH"),
        ("Civil", "CIVIL"),
        ("Information Technology", "IT"),
        ("Artificial Intelligence", "AI"),
    ]
    dept_ids = {}
    with app.app_context():
        for name, code in department_data:
            d = Department(name=name, code=code, university_id=uni_id)
            db.session.add(d)
            db.session.flush()
            dept_ids[code] = d.id
        db.session.commit()
    print(f"   ✓ {len(department_data)} departments created")

    # Refresh dept_ids from the DB for safety
    with app.app_context():
        dept_ids = {d.code: d.id for d in Department.query.all()}

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
    with app.app_context():
        for dept_code, courses in course_defs.items():
            for code, name, credits, diff, ctype in courses:
                c = Course(
                    code=code,
                    name=name,
                    credits=credits,
                    difficulty=diff,
                    course_type=ctype,
                    department_id=dept_ids[dept_code],
                )
                db.session.add(c)
                db.session.flush()
                course_ids[code] = c.id
                total_courses += 1
        db.session.commit()
    print(f"   ✓ {total_courses} courses created")

    with app.app_context():
        courses_all = [
            {"id": c.id, "code": c.code, "name": c.name, "department_id": c.department_id}
            for c in Course.query.all()
        ]
    courses_by_dept = {}
    for c in courses_all:
        courses_by_dept.setdefault(c["department_id"], []).append(c)

    # Timeslots needed for faculty availability
    with app.app_context():
        university = University.query.first()
        timeslots = json.loads(university.timeslots) if university.timeslots else []
        days_list = json.loads(university.days) if university.days else []

    # ── 4. Faculty ─────────────────────────────────────────────
    print("👨‍🏫  Creating faculty...")
    faculty_defs = {
        "CSE": [
            ("FAC001", "Dr. Rajesh Kumar",     ["CS101", "CS102"]),
            ("FAC002", "Prof. Anita Sharma",     ["CS103", "CS108"]),
            ("FAC003", "Dr. Vikram Patel",       ["CS104", "CS105"]),
            ("FAC004", "Prof. Meera Reddy",      ["CS106", "CS107"]),
        ],
        "ECE": [
            ("FAC005", "Dr. Suresh Babu",        ["EC101", "EC102"]),
            ("FAC006", "Prof. Lakshmi Devi",     ["EC103", "EC105"]),
            ("FAC007", "Dr. Arjun Rao",          ["EC104", "EC106"]),
        ],
        "MECH": [
            ("FAC008", "Dr. Prakash Joshi",     ["ME101", "ME102"]),
            ("FAC009", "Prof. Kavitha Nair",     ["ME103", "ME106"]),
            ("FAC010", "Dr. Raman Singh",        ["ME104", "ME105"]),
        ],
        "CIVIL": [
            ("FAC011", "Dr. Sunita Patel",       ["CE101", "CE102"]),
            ("FAC012", "Prof. Arun Kumar",       ["CE103", "CE104", "CE105"]),
        ],
        "IT": [
            ("FAC013", "Dr. Deepa Menon",        ["IT101", "IT102"]),
            ("FAC014", "Prof. Karthik Iyer",     ["IT103", "IT104", "IT105"]),
        ],
        "AI": [
            ("FAC015", "Dr. Priya Krishnan",     ["AI101", "AI102"]),
            ("FAC016", "Prof. Sanjay Gupta",     ["AI103", "AI104"]),
            ("FAC017", "Dr. Nisha Verma",       ["AI105", "AI106"]),
        ],
    }

    total_faculty = 0
    avail = {day: timeslots for day in days_list}
    with app.app_context():
        for dept_code, facs in faculty_defs.items():
            for uid, name, course_codes in facs:
                cids = [course_ids[c] for c in course_codes if c in course_ids]
                f = Faculty(
                    faculty_uid=uid,
                    name=name,
                    department_id=dept_ids[dept_code],
                    available_slots=json.dumps(avail)
                )
                # Add M2M courses
                for cid in cids:
                    c = Course.query.get(cid)
                    if c:
                        f.courses_can_teach.append(c)
                db.session.add(f)
                total_faculty += 1
        db.session.commit()
    print(f"   ✓ {total_faculty} faculty members created")

    # ── 5. Students ────────────────────────────────────────────
    print("🎓  Enrolling students...")
    first_names = [
        "Aarav", "Aditi", "Arjun", "Diya", "Ishaan", "Kavya", "Rohan", "Priya",
        "Vivaan", "Ananya", "Siddharth", "Neha", "Aditya", "Pooja", "Rahul",
        "Shreya", "Vihaan", "Riya", "Karan", "Sakshi", "Dev", "Tanvi", "Nikhil",
        "Anjali", "Manish", "Divya", "Akash", "Simran", "Varun", "Meghna",
        "Harsh", "Kritika", "Rajat", "Swati", "Pranav", "Nandini", "Gaurav",
        "Isha", "Kunal", "Tanya",
    ]
    last_names = [
        "Sharma", "Patel", "Kumar", "Singh", "Reddy", "Gupta", "Nair", "Iyer",
        "Joshi", "Verma", "Chauhan", "Mehta", "Rao", "Das", "Bhat", "Malhotra",
        "Pillai", "Mishra", "Saxena", "Agarwal",
    ]

    total_students = 0
    stu_counter = 1
    with app.app_context():
        for dept_code, did in dept_ids.items():
            dept_courses = courses_by_dept.get(did, [])
            num_students = random.randint(45, 80)
            for _ in range(num_students):
                fname = random.choice(first_names)
                lname = random.choice(last_names)
                num_enroll = min(len(dept_courses), random.randint(4, 6))
                enrolled = random.sample([c["id"] for c in dept_courses], num_enroll)

                s = Student(
                    student_uid=f"STU{stu_counter:04d}",
                    name=f"{fname} {lname}",
                    department_id=did,
                )
                db.session.add(s)
                db.session.flush()
                for cid in enrolled:
                    c = Course.query.get(cid)
                    if c:
                        s.courses_enrolled.append(c)
                stu_counter += 1
                total_students += 1
        db.session.commit()
    print(f"   ✓ {total_students} students enrolled")

    # ── 6. Generate Sections ───────────────────────────────────
    print("👥  Generating sections...")
    from blueprints.api import generate_sections
    with app.app_context():
        result = generate_sections()
        msg = result[0].get("message", "Sections generated") if isinstance(result, tuple) else "Sections generated"
    print(f"   ✓ {msg}")

    # ── 7. Generate Timetable ──────────────────────────────────
    print("⚡  Generating timetable...")
    from blueprints.api import generate_timetable
    with app.app_context():
        result = generate_timetable()
        msg = result[0].get("message", "Done") if isinstance(result, tuple) else "Done"
        conflicts = result[0].get("conflicts", []) if isinstance(result, tuple) else []
    print(f"   ✓ {msg}")
    if conflicts:
        print(f"   ⚠ {len(conflicts)} conflicts detected")

    # ── Summary ────────────────────────────────────────────────
    with app.app_context():
        print("\n" + "=" * 50)
        print("📊 DASHBOARD SUMMARY")
        print(f"   Departments:      {Department.query.count()}")
        print(f"   Courses:          {Course.query.count()}")
        print(f"   Faculty:          {Faculty.query.count()}")
        print(f"   Students:         {Student.query.count()}")
        print(f"   Sections:         {Section.query.count()}")
        print(f"   Timetable Slots:  {TimetableEntry.query.count()}")
        print("=" * 50)
    print("✅ Seed complete!")


if __name__ == "__main__" or True:
    try:
        _seed()
    except Exception as e:
        print(f"Seed failed: {e}")
        import traceback

        traceback.print_exc()
        # Don't exit with error code — just warn and continue so deployment doesn't crash.
        print("⚠️  Continuing despite seed failure.")
