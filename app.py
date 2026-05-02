"""
UniSchedule — University Timetable Management System
"""
import os, sys
from flask import Flask, redirect
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from dotenv import load_dotenv
from models import db

# ─── Load environment ───────────────────────────────────────
load_dotenv()

# ─── Mandatory env var checks ───────────────────────────────
_secret_key = os.getenv('FLASK_SECRET_KEY')
if not _secret_key:
    sys.exit("FATAL: FLASK_SECRET_KEY is not set.")

_admin_password = os.getenv('ADMIN_PASSWORD')
if not _admin_password:
    sys.exit("FATAL: ADMIN_PASSWORD is not set.")

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

# ─── Extensions ─────────────────────────────────────────────
csrf = CSRFProtect(app)
db.init_app(app)
migrate = Migrate(app, db)

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

@app.route('/')
def index():
    return redirect('/login')

# ─── CSRF Exemptions ────────────────────────────────────────
csrf.exempt(api)
csrf.exempt(auth)
csrf.exempt(student_bp)
csrf.exempt(faculty_bp)
csrf.exempt(chatbot_admin_bp)
csrf.exempt(chatbot_faculty_bp)
csrf.exempt(chatbot_student_bp)
csrf.exempt(attendance_bp)
csrf.exempt(complaints_bp)

# ─── Run ────────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
    app.run(host='0.0.0.0', debug=debug, port=port)
