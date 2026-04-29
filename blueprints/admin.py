"""
Admin blueprint — page routes for admin dashboard and setup pages.
"""
from flask import Blueprint, render_template, session, redirect, url_for

from blueprints.utils import login_required, role_required

admin = Blueprint('admin', __name__)


@admin.route('/app')
def standalone_app():
    return render_template('unischedule.html')


@admin.route('/')
@login_required
def dashboard():
    if session.get('role') == 'faculty':
        return redirect(url_for('faculty_bp.timetable_faculty_page'))
    if session.get('role') == 'student':
        return redirect(url_for('student_bp.student_app'))
    return render_template('dashboard.html')


@admin.route('/university')
@login_required
@role_required('admin')
def university_page():
    return render_template('university.html')


@admin.route('/departments')
@login_required
@role_required('admin')
def departments_page():
    return render_template('departments.html')


@admin.route('/courses')
@login_required
@role_required('admin')
def courses_page():
    return render_template('courses.html')


@admin.route('/faculty')
@login_required
@role_required('admin')
def faculty_page():
    return render_template('faculty.html')


@admin.route('/students')
@login_required
@role_required('admin')
def students_page():
    return render_template('students.html')


@admin.route('/sections')
@login_required
@role_required('admin')
def sections_page():
    return render_template('sections.html')


@admin.route('/timetable/generate')
@login_required
@role_required('admin')
def generate_page():
    return render_template('generate.html')


@admin.route('/timetable/section')
@login_required
def timetable_section_page():
    return render_template('timetable_section.html')


@admin.route('/timetable/rooms')
@login_required
@role_required('admin')
def timetable_rooms_page():
    return render_template('timetable_rooms.html')

@admin.route('/room-utilization')
@login_required
@role_required('admin')
def room_utilization_page():
    return render_template('room_utilization.html')
