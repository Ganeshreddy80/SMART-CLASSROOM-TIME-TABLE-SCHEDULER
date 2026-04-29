import sys, os
import datetime
import random
import json
import math

# Allow imports from the project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app, db
from models import TimetableEntry, Section, Student, Faculty, Course, Department, Classroom, University
from models import section_students, student_courses, faculty_courses
from models import generate_email_from_name, ensure_unique_email
from timetable_generator import generate_timetable

def seed():
    with app.app_context():
        print(f"DEBUG: Database URI is {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"DEBUG: Instance path is {app.instance_path}")
        db.create_all()
        print("🗑️  Clearing existing data...")
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

        # 1. University Setup
        print("🏛️  Setting up university...")
        uni = University(
            name="SRM University AP",
            total_blocks=4,
            floors_per_block=json.dumps({"1": 3, "2": 4, "3": 2, "4": 3}),
            rooms_per_block=5,
            room_capacity=80,
            days=json.dumps(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]),
            timeslots=json.dumps([
                "9:00-10:00", "10:00-11:00", "11:00-12:00",
                "12:00-1:00", "2:00-3:00", "3:00-4:00", "4:00-5:00"
            ])
        )
        db.session.add(uni)
        
        # 2. Classrooms
        for b in range(1, 5):
            for f in range(1, 5): 
                for r in range(1, 6):
                    cr = Classroom(room_number=f"{b}{f}{r:02d}", capacity=80, block=str(b))
                    db.session.add(cr)
        db.session.commit()

        # 3. Departments
        print("🏢  Creating departments...")
        departments_data = [
            ("Computer Science", "CSE"),
            ("Electronics", "ECE"),
            ("Mechanical", "MECH"),
            ("Civil", "CIVIL"),
            ("Information Technology", "IT"),
            ("Artificial Intelligence", "AI"),
        ]
        dept_map = {}
        for name, code in departments_data:
            d = Department(name=name, code=code)
            db.session.add(d)
            db.session.flush() # Get ID
            dept_map[code] = d
        db.session.commit()

        # 4. Courses
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
        
        course_map = {}
        for code, courses in course_defs.items():
            dept = dept_map[code]
            for c_code, name, credits, diff, ctype in courses:
                c = Course(
                    code=c_code, name=name, credits=credits,
                    difficulty=diff, course_type=ctype,
                    department_id=dept.id,
                    classes_per_week=4 if ctype == 'Theory' else 2
                )
                db.session.add(c)
                db.session.flush()
                course_map[c_code] = c
        db.session.commit()

        # 5. Faculty
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
        
        all_ts = [
            "9:00-10:00", "10:00-11:00", "11:00-12:00",
            "12:00-1:00", "2:00-3:00", "3:00-4:00", "4:00-5:00"
        ]
        days_list = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        avail_full = {day: all_ts for day in days_list}

        for code, facs in faculty_defs.items():
            dept = dept_map[code]
            for uid, name, c_codes in facs:
                raw_email = generate_email_from_name(name)
                email = ensure_unique_email(raw_email)
                f = Faculty(
                    faculty_uid=uid, name=name,
                    email=email,
                    department_id=dept.id,
                    available_slots=json.dumps(avail_full)
                )
                f.set_password("faculty123")
                f.courses_can_teach = [course_map[cc] for cc in c_codes if cc in course_map]
                db.session.add(f)
        db.session.commit()

        # 6. Students
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

        stu_counter = 1
        for code, dept in dept_map.items():
            num_students = random.randint(45, 80)
            dept_courses = [c for c in Course.query.filter_by(department_id=dept.id).all()]
            
            for _ in range(num_students):
                fname = random.choice(first_names)
                lname = random.choice(last_names)
                s = Student(
                    student_uid=f"STU{stu_counter:04d}",
                    name=f"{fname} {lname}",
                    department_id=dept.id,
                    email=f"{fname.lower()}.{lname.lower()}{stu_counter}@srmap.edu.in"
                )
                s.set_password("student123")
                # Enroll in 4-6 courses
                num_enroll = min(len(dept_courses), random.randint(4, 6))
                s.courses_enrolled = random.sample(dept_courses, num_enroll)
                db.session.add(s)
                stu_counter += 1
        db.session.commit()

        # 7. Generate Sections
        print("👥  Generating sections...")
        for dept in Department.query.all():
            students = Student.query.filter_by(department_id=dept.id).all()
            total = len(students)
            if total == 0: continue
            
            num_sections = math.ceil(total / 60)
            per_section = math.ceil(total / num_sections)
            
            for i in range(num_sections):
                section_name = chr(65 + i)
                start = i * per_section
                end = min(start + per_section, total)
                section_students_list = students[start:end]
                
                sec = Section(
                    name=section_name,
                    department_id=dept.id,
                    student_count=len(section_students_list)
                )
                sec.students = section_students_list
                db.session.add(sec)
        db.session.commit()

        # 8. Generate Timetable
        print("⚡  Generating timetable...")
        result = generate_timetable()
        print(f"   ✓ {result.get('message', 'Done')}")
        if result.get('conflicts'):
            print(f"   ⚠ {len(result['conflicts'])} conflicts detected")

        print("\n✅ Seed and Generation complete!")

if __name__ == "__main__":
    seed()
