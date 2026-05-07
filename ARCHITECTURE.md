# UniSchedule Architecture

## System Design

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Browser                         │
│                    (Jinja2 + Vanilla JS)                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Gunicorn Server                         │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                    Flask App (app.py)                │  │
│  │  ┌───────────┬───────────┬───────────┐              │  │
│  │  │   Auth    │   Admin   │  Faculty  │              │  │
│  │  │  Blueprint│  Blueprint│  Blueprint│              │  │
│  │  ├───────────┼───────────┼───────────┤              │  │
│  │  │  Student  │    API    │ Attendance│              │  │
│  │  │  Blueprint│  Blueprint│  Blueprint│              │  │
│  │  ├───────────┼───────────┼───────────┤              │  │
│  │  │Complaints │Anomalies  │ Chatbots  │              │  │
│  │  │  Blueprint│  Blueprint│  (x3)     │              │  │
│  │  └───────────┴───────────┴───────────┘              │  │
│  │                    Flask-WTF (CSRF)                   │  │
│  └─────────────────────────────────────────────────────┘  │
│                              │                              │
│                              ▼                              │
│                    SQLAlchemy ORM + Alembic                 │
│                              │                              │
│                    ┌───────────────┐                       │
│                    │   Database    │                       │
│                    │ SQLite / PG │                       │
│                    └───────────────┘                       │
│                              │
└──────────────────────────────┼──────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   OpenRouter API    │
                    │   (GPT-4o-mini)    │
                    └─────────────────────┘
```

---

## Database Schema (ER Diagram)

```
university
├── id (PK)
├── name
├── total_blocks
├── rooms_per_block
├── days
├── timeslots
└── created_at

department
├── id (PK)
├── code
├── name
└── university_id

course
├── id (PK)
├── code
├── name
├── credits
├── difficulty
├── course_type
├── classes_per_week
└── department_id → department.id

faculty
├── id (PK)
├── faculty_uid
├── name
├── email
├── phone
├── password_hash
├── photo_url
├── short_name
└── department_id → department.id

student
├── id (PK)
├── student_uid
├── name
├── email
├── password_hash
├── photo_url
├── enrollment_year
└── department_id → department.id

section
├── id (PK)
├── name
├── student_count
└── department_id → department.id

classroom
├── id (PK)
├── block
├── floor
└── room_number

timetable_entry
├── id (PK)
├── day
├── timeslot
├── course_id → course.id
├── faculty_id → faculty.id
├── section_id → section.id
├── classroom_id → classroom.id
└── is_replacement (bool)

attendance
├── id (PK)
├── student_id → student.id
├── course_id → course.id
├── section_id → section.id
├── date
└── status (present/absent/od)

faculty_absence
├── id (PK)
├── faculty_id → faculty.id
├── date
├── slots (JSON)
└── reason

password_reset_token
├── id (PK)
├── email
├── otp_hash
├── reset_token
├── created_at
├── expires_at
└── used

complaint
├── id (PK)
├── title
├── description
├── category
├── status
├── reply
├── reply_suggestion
├── created_at
└── updated_at

anomaly
├── id (PK)
├── title
├── description
├── category
├── severity
├── status
├── auto_dismissible
├── created_at
└── resolved_at
```

---

## Component Overview

### `app.py`
- Flask application factory
- Environment variable validation (`_validate_config()`)
- Blueprint registration (10 blueprints)
- CSRF exemptions for API routes
- Health check endpoint (`/health`)
- Request logging middleware

### Blueprints

| Blueprint | File | Routes | Role |
|-----------|------|--------|------|
| Auth | `blueprints/auth.py` | 6 | Public |
| Admin | `blueprints/admin.py` | 2 | Admin |
| Faculty | `blueprints/faculty.py` | 6 | Faculty |
| Student | `blueprints/student.py` | 17 | Student |
| API | `blueprints/api.py` | 39 | Mixed |
| Attendance | `blueprints/attendance.py` | 16 | Faculty/Student |
| Complaints | `blueprints/complaints.py` | 7 | Mixed |
| Anomalies | `blueprints/anomalies.py` | 5 | Admin |
| Chatbots | `blueprints/chatbot_*.py` | 3 | Mixed |

### Caching Strategy
- **AI Context Cache**: 60-second TTL, thread-safe (`api.py`)
- **Session Store**: Client-side Flask signed cookies
- **Date Helpers**: Shared module (`utils/date_helpers.py`)

### Security
- Session-based authentication with `permanent=True` for faculty/student
- OTP-based password reset with 5-minute expiry
- CSRF protection (WTForms) with exemptions for API routes
- Config validation at startup (min lengths, URL schemes)
- Input sanitization on chat endpoints

### Deployment
- **Development**: `python app.py` (Flask dev server)
- **Production**: `gunicorn app:app` (Heroku-ready)
- **Worker**: Background process for async tasks (Procfile)
- **Health Check**: `GET /health` with DB probe