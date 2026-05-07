# UniSchedule — Smart Classroom Time Table Scheduler

A full-stack **Flask + SQLAlchemy** web application for automating university timetable generation, attendance management, and AI-powered academic assistance.

---

## Features

- **Automated Timetable Generation** — Generates conflict-free schedules for departments, sections, and faculty
- **Multi-role Access** — Admin, Faculty, and Student portals
- **QR-based Attendance** — Face-verified attendance with live session tracking
- **AI Chatbot** — Context-aware chatbot powered by OpenRouter (GPT-4o-mini) for admin, faculty, and students
- **Real-time Analytics** — Room utilization, faculty workload, low-attendance alerts
- **Complaint Management** — NLP-based complaint categorization and auto-suggestions
- **Email Notifications** — OTP-based password reset via SMTP
- **Anomaly Detection** — Detects schedule conflicts, overloads, and missing data

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3, Flask, SQLAlchemy, WTForms |
| Frontend | Jinja2, vanilla JS, Bootstrap |
| Database | SQLite (dev) / PostgreSQL (prod) |
| AI | OpenRouter API (GPT-4o-mini) |
| Deployment | Gunicorn, Heroku-ready |

---

## Quick Start

1. Clone the repo
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in values
4. Run migrations:
   ```bash
   flask db upgrade
   ```
5. Start the app:
   ```bash
   python app.py
   ```

---

## Environment Variables

See [`.env.example`](.env.example) for the complete list. Key variables:

| Variable | Description |
|----------|-------------|
| `FLASK_SECRET_KEY` | Flask session secret (min 16 chars) |
| `DATABASE_URL` | SQLAlchemy DB URI |
| `ADMIN_PASSWORD` | Default admin password (min 8 chars) |
| `OPENROUTER_API_KEY` | AI chatbot API key |
| `SMTP_USER` / `SMTP_PASS` | Email OTP credentials |
| `GOOGLE_MAPS_API_KEY` | Map features (optional) |

---

## Project Structure

```
├── app.py                  # Flask app factory, config, blueprints
├── models.py               # SQLAlchemy ORM models
├── requirements.txt        # Pinned Python dependencies
├── .env.example            # Environment variable template
├── blueprints/             # Route modules (auth, admin, faculty, student, api, attendance, complaints, anomalies)
├── utils/                  # Shared helpers (date parsing, etc.)
├── static/                 # CSS, JS, images
└── templates/              # Jinja2 HTML templates
```

---

## API Documentation

See [API.md](API.md) for detailed endpoint documentation.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for system design and database schema.

---

## Testing

```bash
pytest
```

## License

MIT