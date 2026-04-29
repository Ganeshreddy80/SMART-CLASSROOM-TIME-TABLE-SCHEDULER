"""
Shared utilities — auth decorators, email helper, admin password, constants.
"""
from functools import wraps
import os, smtplib, random

from flask import session, request, jsonify, redirect, url_for
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.security import generate_password_hash, check_password_hash


# ─── Constants ───────────────────────────────────────────────
ADMIN_EMAIL = 'admin@srmap.edu.in'


# ─── Admin Password ─────────────────────────────────────────
_ADMIN_PASSWORD_HASH = None

def get_admin_password_hash():
    """Lazy-init admin password hash from ADMIN_PASSWORD env var."""
    global _ADMIN_PASSWORD_HASH
    if _ADMIN_PASSWORD_HASH is None:
        password = os.environ['ADMIN_PASSWORD']  # guaranteed set by app startup check
        _ADMIN_PASSWORD_HASH = generate_password_hash(password, method='pbkdf2:sha256')
    return _ADMIN_PASSWORD_HASH

def reset_admin_password_hash(new_password):
    """Update the in-memory admin password hash (used by password reset flow)."""
    global _ADMIN_PASSWORD_HASH
    _ADMIN_PASSWORD_HASH = generate_password_hash(new_password, method='pbkdf2:sha256')


# ─── Auth Decorators ─────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Unauthorized'}), 401
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session:
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Unauthorized'}), 401
                return redirect(url_for('auth.login_page'))
            if session['role'] not in allowed_roles and session['role'] != 'admin':
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Forbidden'}), 403
                return redirect(url_for('auth.login_page'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ─── SMTP / OTP Email ────────────────────────────────────────
def send_otp_email(to_email, otp):
    """Send OTP email via SMTP."""
    smtp_email = os.getenv('SMTP_EMAIL', '')
    smtp_password = os.getenv('SMTP_PASSWORD', '')

    if not smtp_email or not smtp_password:
        print(f"[DEBUG] SMTP not configured. OTP for {to_email}: {otp}")
        return True  # Return True so flow continues in dev mode

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'UniSchedule - Password Reset OTP'
        msg['From'] = smtp_email
        msg['To'] = to_email

        html = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 30px; background: #f8f9fa; border-radius: 12px;">
            <div style="text-align: center; margin-bottom: 24px;">
                <h2 style="color: #1a1a2e; margin: 0;">📚 UniSchedule</h2>
                <p style="color: #666; font-size: 14px; margin-top: 4px;">Password Reset Request</p>
            </div>
            <div style="background: white; padding: 24px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
                <p style="color: #333; margin-top: 0;">You requested a password reset. Use the OTP below:</p>
                <div style="text-align: center; margin: 24px 0;">
                    <div style="display: inline-block; background: linear-gradient(135deg, #e8a838, #f0c040); color: #1a1a2e; font-size: 32px; font-weight: 700; letter-spacing: 8px; padding: 16px 32px; border-radius: 8px;">
                        {otp}
                    </div>
                </div>
                <p style="color: #666; font-size: 13px; text-align: center;">This OTP expires in <strong>5 minutes</strong>.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px; margin-bottom: 0;">If you didn't request this, please ignore this email. Your password will remain unchanged.</p>
            </div>
        </div>
        """
        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[SMTP ERROR] {e}")
        return False


# ─── Helpers ─────────────────────────────────────────────────
def calc_classes_per_week(difficulty, credits):
    if difficulty == 'Hard' and credits >= 5:
        return 5
    elif difficulty == 'Medium' and credits >= 4:
        return 4
    elif difficulty == 'Easy' and credits <= 3:
        return 3
    else:
        return credits
