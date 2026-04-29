"""
Auth blueprint — login, logout, forgot password, OTP reset.
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import random, secrets

from models import (db, Faculty, Student, PasswordResetToken)
from blueprints.utils import (
    ADMIN_EMAIL, get_admin_password_hash, reset_admin_password_hash,
    send_otp_email
)

auth = Blueprint('auth', __name__)


@auth.route('/debug-users')
def debug_users():
    from models import Faculty, Student
    faculty = Faculty.query.limit(3).all()
    students = Student.query.limit(3).all()
    result = "FACULTY:\n"
    for f in faculty:
        result += f"{f.email} | hash_exists={bool(f.password_hash)}\n"
    result += "\nSTUDENTS:\n"
    for s in students:
        result += f"{s.email} | hash_exists={bool(s.password_hash)}\n"
    return result, 200, {'Content-Type': 'text/plain'}


@auth.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        # Validate email format
        if not email or not email.endswith('@srmap.edu.in'):
            return render_template('login.html', error='Wrong credentials')

        if not password:
            return render_template('login.html', error='Wrong credentials')

        # Check admin
        if email == ADMIN_EMAIL:
            if check_password_hash(get_admin_password_hash(), password):
                session['role'] = 'admin'
                session['user_id'] = 'admin'
                session['user_name'] = 'Admin User'
                return redirect(url_for('admin.dashboard'))
            else:
                return render_template('login.html', error='Wrong credentials')

        # Check faculty
        f = Faculty.query.filter_by(email=email).first()
        if f and f.check_password(password):
            session.permanent = True
            session['role'] = 'faculty'
            session['user_id'] = f.id
            session['user_name'] = f.name
            session['user_email'] = f.email
            return redirect(url_for('faculty_bp.faculty_app', email=f.email))

        # Check student
        s = Student.query.filter_by(email=email).first()
        if s and s.check_password(password):
            session.permanent = True
            session['role'] = 'student'
            session['user_id'] = s.id
            session['user_name'] = s.name
            session['department_id'] = s.department_id
            student_sections = [sec.id for sec in s.sections]
            session['section_ids'] = student_sections
            return redirect(url_for('student_bp.student_app'))

        return render_template('login.html', error='Wrong credentials')

    return render_template('login.html')


@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login_page'))


# ─── Forgot Password Routes ──────────────────────────────────
@auth.route('/forgot-password')
def forgot_password_page():
    return render_template('forgot_password.html')


@auth.route('/api/forgot-password', methods=['POST'])
def api_forgot_password():
    data = request.json
    email = data.get('email', '').strip().lower()

    # Validate email format
    if not email or not email.endswith('@srmap.edu.in'):
        return jsonify({'error': 'Please enter a valid @srmap.edu.in email'}), 400

    # Check if email exists
    user = Faculty.query.filter_by(email=email).first()
    if not user:
        user = Student.query.filter_by(email=email).first()
    if not user:
        if email == ADMIN_EMAIL:
            pass  # Admin can also reset
        else:
            return jsonify({'error': 'Email not registered'}), 404

    # Invalidate any existing tokens for this email
    PasswordResetToken.query.filter_by(email=email, used=False).update({'used': True})
    db.session.commit()

    # Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))

    # Store hashed OTP
    token = PasswordResetToken(
        email=email,
        expires_at=datetime.utcnow() + timedelta(minutes=5)
    )
    token.set_otp(otp)
    db.session.add(token)
    db.session.commit()

    # Send email
    sent = send_otp_email(email, otp)
    if not sent:
        return jsonify({'error': 'Failed to send email. Please try again.'}), 500

    return jsonify({'message': 'OTP sent to your email. Check your inbox.'})


@auth.route('/api/verify-otp', methods=['POST'])
def api_verify_otp():
    data = request.json
    email = data.get('email', '').strip().lower()
    otp = data.get('otp', '').strip()

    if not email or not otp:
        return jsonify({'error': 'Email and OTP are required'}), 400

    # Find the latest unused token for this email
    token = PasswordResetToken.query.filter_by(
        email=email, used=False
    ).order_by(PasswordResetToken.created_at.desc()).first()

    if not token:
        return jsonify({'error': 'No OTP request found. Please request a new OTP.'}), 400

    if token.is_expired():
        token.used = True
        db.session.commit()
        return jsonify({'error': 'OTP has expired. Please request a new one.'}), 400

    if not token.check_otp(otp):
        return jsonify({'error': 'Invalid OTP. Please try again.'}), 400

    # Generate a one-time reset token
    reset_token = secrets.token_urlsafe(32)
    token.reset_token = reset_token
    db.session.commit()

    return jsonify({'message': 'OTP verified', 'reset_token': reset_token})


@auth.route('/api/reset-password', methods=['POST'])
def api_reset_password():
    data = request.json
    reset_token = data.get('reset_token', '').strip()
    new_password = data.get('new_password', '').strip()

    if not reset_token or not new_password:
        return jsonify({'error': 'Reset token and new password are required'}), 400

    if len(new_password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    # Find the token
    token = PasswordResetToken.query.filter_by(reset_token=reset_token, used=False).first()
    if not token:
        return jsonify({'error': 'Invalid or expired reset link. Please request a new OTP.'}), 400

    if token.is_expired():
        token.used = True
        db.session.commit()
        return jsonify({'error': 'Reset link has expired. Please request a new OTP.'}), 400

    email = token.email

    # Update password
    if email == ADMIN_EMAIL:
        reset_admin_password_hash(new_password)
    else:
        user = Faculty.query.filter_by(email=email).first()
        if not user:
            user = Student.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        user.set_password(new_password)

    # Mark token as used
    token.used = True
    db.session.commit()

    return jsonify({'message': 'Password reset successful! You can now login with your new password.'})
