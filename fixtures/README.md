# Fixtures

This folder contains database seeding scripts for the UniSchedule application.

## seed_data.py

Populates the database with realistic university data including:
- **6 departments** (CSE, ECE, MECH, CIVIL, IT, AI)
- **36 courses** across all departments
- **17 faculty members** with course assignments
- **~300–480 students** randomly distributed
- **Auto-generated sections** (60 students per section)
- **Auto-generated timetable** (conflict-free)

### Prerequisites

1. The Flask server must be running first
2. `ADMIN_PASSWORD` must be set in `.env`

### How to Use

```bash
# Terminal 1 — Start the server
python3 app.py

# Terminal 2 — Run the seed script
python3 fixtures/seed_data.py
```

### What It Does

1. **Clears** all existing data (departments, courses, faculty, students, sections, timetable)
2. **Creates** departments, courses, and faculty via the API
3. **Enrolls** students with random course selections
4. **Generates** sections (auto-split by department, 60 per section)
5. **Generates** a conflict-free timetable

### Default Credentials

After seeding, you can log in with:

| Role    | Email                          | Password      |
|---------|--------------------------------|---------------|
| Admin   | `admin@srmap.edu.in`           | *(from .env)* |
| Faculty | `firstname.lastname@srmap.edu.in` | `firstname@123` |
| Student | `firstname.lastname@srmap.edu.in` | `firstname@123` |

> **Note:** Faculty and student passwords follow the pattern `{lowercase_first_name}@123`.
> For example, faculty "Dr. Rajesh Kumar" → email `rajesh.kumar@srmap.edu.in`, password `rajesh@123`.
