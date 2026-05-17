"""
UniSchedule — University Timetable Management System
"""
import os, sys
from flask import Flask, redirect
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv
from models import db

# ─── Load environment ───────────────────────────────────────
load_dotenv()

# ─── Mandatory env var checks ───────────────────────────────
def _validate_config():
    """Validate all required configuration on startup."""
    required_vars = {
        'FLASK_SECRET_KEY': 'Flask secret key (min 16 chars)',
        'ADMIN_PASSWORD': 'Admin login password (min 8 chars)',
    }
    errors = []
    for var, desc in required_vars.items():
        val = os.getenv(var)
        if not val:
            errors.append(f"  - {var}: {desc}")
    
    # Validate specific constraints
    secret_key = os.getenv('FLASK_SECRET_KEY', '')
    if len(secret_key) < 16:
        errors.append(f"  - FLASK_SECRET_KEY: must be at least 16 characters (got {len(secret_key)})")
    
    admin_password = os.getenv('ADMIN_PASSWORD', '')
    if len(admin_password) < 8:
        errors.append(f"  - ADMIN_PASSWORD: must be at least 8 characters (got {len(admin_password)})")
    
    db_url = os.getenv('DATABASE_URL', 'sqlite:///university.db')
    if not db_url.startswith(('sqlite://', 'postgresql://', 'postgres://', 'mysql://')):
        errors.append(f"  - DATABASE_URL: unsupported database URL scheme")
    
    if errors:
        print("FATAL: Configuration validation failed:\n" + "\n".join(errors))
        sys.exit(1)

_validate_config()

_secret_key = os.environ['FLASK_SECRET_KEY']
_admin_password = os.environ['ADMIN_PASSWORD']

# ─── Create app ─────────────────────────────────────────────
app = Flask(__name__)

db_url = os.getenv('DATABASE_URL', 'sqlite:///university.db')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = _secret_key
app.config['SESSION_COOKIE_NAME'] = 'unischedule_session'
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV', 'production') == 'production'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 86400
app.config['WTF_CSRF_TIME_LIMIT'] = 86400

# ─── CORS configuration ──────────────────────────────────────────────────────
# Read allowed origins from env; default to local dev.  In production set
# CORS_ALLOWED_ORIGINS=https://yourdomain.com https://app.yourdomain.com
cors_origins = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:5000,http://127.0.0.1:5000')
allowed_origins = [o.strip() for o in cors_origins.split(',') if o.strip()]
CORS(app, origins=allowed_origins, supports_credentials=True)

# ─── Extensions ─────────────────────────────────────────────
csrf = CSRFProtect(app)
db.init_app(app)
migrate = Migrate(app, db)

# ─── Create tables if they don't exist (fallback for fresh deploys) ───
with app.app_context():
    db.create_all()


@app.cli.command("seed-admin")
def seed_admin():
    from werkzeug.security import generate_password_hash
    from models import Student, Department
    admin_email = os.getenv('SMART_ADMIN_EMAIL', 'admin@srmap.edu.in')
    admin_pass = os.getenv('ADMIN_PASSWORD')
    if not admin_pass:
        print("No ADMIN_PASSWORD set, skipping")
        return
    try:
        if not Student.query.filter_by(email=admin_email).first():
            dept = Department.query.first()
            if not dept:
                dept = Department(name='Admin', code='ADM')
                db.session.add(dept)
                db.session.flush()
            admin = Student(
                student_uid='ADMIN001',
                name='Admin',
                email=admin_email,
                password_hash=generate_password_hash(admin_pass),
                role='admin',
                department_id=dept.id
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin created!")
    except Exception as e:
        print(f"Seed failed: {e}")
        db.session.rollback()

# ─── Register Blueprints ────────────────────────────────────
from blueprints.auth import auth
from blueprints.admin import admin
from blueprints.faculty import faculty_bp
from blueprints.student import student_bp
from blueprints.api import api
from blueprints.chatbot_admin import chatbot_admin_bp
from blueprints.chatbot_faculty import chatbot_faculty_bp
from blueprints.chatbot_student import chatbot_student_bp
from blueprints.attendance import attendance_bp
from blueprints.complaints import complaints_bp
from blueprints.anomalies import anomalies_bp

app.register_blueprint(auth)
app.register_blueprint(admin)
app.register_blueprint(faculty_bp)
app.register_blueprint(student_bp)
app.register_blueprint(chatbot_student_bp)
app.register_blueprint(api)
app.register_blueprint(attendance_bp)
app.register_blueprint(chatbot_admin_bp)
app.register_blueprint(chatbot_faculty_bp)
app.register_blueprint(complaints_bp)
app.register_blueprint(anomalies_bp)

@app.route('/')
def index():
    from flask import render_template
    return render_template('landing.html')

@app.route('/health')
def health():
    """Health check endpoint for monitoring and load balancers."""
    try:
        from sqlalchemy import text
        from models import db
        db.session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"

    import time
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "timestamp": time.time()
    }

# ─── Request Logging Middleware ─────────────────────────────
@app.before_request
def log_request():
    """Log every incoming request with method, path, and remote address."""
    from flask import request
    import logging, time
    app.logger.setLevel(logging.INFO)
    if not app.debug:
        app.logger.info(f"{request.method} {request.path} [{request.remote_addr}]")

# ─── CSRF Exemptions ────────────────────────────────────────
csrf.exempt(auth)
csrf.exempt(api)
csrf.exempt(student_bp)
csrf.exempt(faculty_bp)
csrf.exempt(chatbot_admin_bp)
csrf.exempt(chatbot_faculty_bp)
csrf.exempt(chatbot_student_bp)
csrf.exempt(attendance_bp)
csrf.exempt(complaints_bp)
csrf.exempt(anomalies_bp)

# ─── Run ────────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.getenv('PORT', os.getenv('FLASK_PORT', 5000)))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
    app.run(host='0.0.0.0', debug=debug, port=port)
