"""
anomaly_engine.py — AI-powered attendance anomaly detection engine.
Call run_all_checks() after any attendance save.
"""
from models import db, Attendance, AttendanceAnomaly, Student, TimetableEntry
from datetime import datetime, date, timedelta
from sqlalchemy import func
import os
import requests

OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')


def call_claude(prompt):
    """Call Claude via OpenRouter for AI analysis."""
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {OPENROUTER_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'anthropic/claude-3-haiku',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 300
            },
            timeout=10
        )
        data = response.json()
        return data['choices'][0]['message']['content']
    except Exception as e:
        return f"AI analysis unavailable: {str(e)}"


def already_flagged(anomaly_type, **kwargs):
    """Check if this exact anomaly was already flagged today."""
    today = date.today()
    query = AttendanceAnomaly.query.filter_by(
        anomaly_type=anomaly_type,
        attendance_date=kwargs.get('attendance_date', today)
    )
    if kwargs.get('affected_student_id'):
        query = query.filter_by(affected_student_id=kwargs['affected_student_id'])
    if kwargs.get('affected_section_id'):
        query = query.filter_by(affected_section_id=kwargs['affected_section_id'])
    return query.first() is not None


def detect_speed_fraud(section_id, course_id, attendance_date):
    """Detect if too many students were marked present too quickly."""
    records = Attendance.query.filter_by(
        section_id=section_id,
        course_id=course_id,
        date=attendance_date,
        status='present'
    ).order_by(Attendance.marked_at).all()

    if len(records) < 5:
        return

    for i in range(len(records) - 9):
        if not records[i].marked_at or not records[i + 9].marked_at:
            continue
        time_diff = (records[i + 9].marked_at - records[i].marked_at).total_seconds()
        if time_diff < 30:
            if already_flagged('speed_fraud',
                               affected_section_id=section_id,
                               attendance_date=attendance_date):
                return

            ai_prompt = f"""
Attendance anomaly detected in a university system.
Type: Speed Fraud
Details: {len(records)} students marked present,
10 of them within {time_diff:.1f} seconds.
Section ID: {section_id}, Course ID: {course_id}
Date: {attendance_date}

Write a 2-sentence admin alert explaining why this is suspicious
and what action to take. Be direct and professional.
"""
            ai_text = call_claude(ai_prompt)

            anomaly = AttendanceAnomaly(
                anomaly_type='speed_fraud',
                severity='critical',
                title=f'⚡ Speed Fraud Detected — Section {section_id}',
                description=f'{len(records)} students marked present, 10 within {time_diff:.0f} seconds',
                ai_analysis=ai_text,
                affected_section_id=section_id,
                affected_course_id=course_id,
                attendance_date=attendance_date,
                raw_data={
                    'total_present': len(records),
                    'suspicious_window_seconds': time_diff,
                    'section_id': section_id,
                    'course_id': course_id
                }
            )
            db.session.add(anomaly)
            db.session.commit()
            return


def detect_sudden_drop(student_id, course_id):
    """Detect if a student's attendance dropped significantly in the last 7 days."""
    today = date.today()
    week_ago = today - timedelta(days=7)
    two_weeks_ago = today - timedelta(days=14)

    recent = Attendance.query.filter(
        Attendance.student_id == student_id,
        Attendance.course_id == course_id,
        Attendance.date >= week_ago,
        Attendance.status == 'present'
    ).count()

    previous = Attendance.query.filter(
        Attendance.student_id == student_id,
        Attendance.course_id == course_id,
        Attendance.date >= two_weeks_ago,
        Attendance.date < week_ago,
        Attendance.status == 'present'
    ).count()

    total_recent = Attendance.query.filter(
        Attendance.student_id == student_id,
        Attendance.course_id == course_id,
        Attendance.date >= week_ago
    ).count()

    if total_recent == 0 or previous == 0:
        return

    recent_pct = (recent / total_recent) * 100
    prev_pct = (previous / total_recent) * 100

    if prev_pct > 70 and recent_pct < 40:
        if already_flagged('sudden_drop',
                           affected_student_id=student_id,
                           attendance_date=today):
            return

        student = Student.query.get(student_id)
        name = student.name if student else f'Student {student_id}'

        ai_prompt = f"""
Student attendance anomaly in a university system.
Student: {name}
Previous week attendance: {prev_pct:.0f}%
Current week attendance: {recent_pct:.0f}%
Drop: {prev_pct - recent_pct:.0f} percentage points

Write a 2-sentence alert for admin/faculty explaining
the concern and recommended action. Professional tone.
"""
        ai_text = call_claude(ai_prompt)

        anomaly = AttendanceAnomaly(
            anomaly_type='sudden_drop',
            severity='warning',
            title=f'📉 Sudden Attendance Drop — {name}',
            description=f'Attendance dropped from {prev_pct:.0f}% to {recent_pct:.0f}% this week',
            ai_analysis=ai_text,
            affected_student_id=student_id,
            affected_course_id=course_id,
            attendance_date=today,
            raw_data={
                'student_id': student_id,
                'previous_pct': prev_pct,
                'recent_pct': recent_pct,
                'drop': prev_pct - recent_pct
            }
        )
        db.session.add(anomaly)
        db.session.commit()


def detect_mass_absent(section_id, course_id, attendance_date):
    """Detect if entire section is absent — possible data error or cancelled class."""
    total = Attendance.query.filter_by(
        section_id=section_id,
        course_id=course_id,
        date=attendance_date
    ).count()

    absent = Attendance.query.filter_by(
        section_id=section_id,
        course_id=course_id,
        date=attendance_date,
        status='absent'
    ).count()

    if total < 5:
        return

    absent_pct = (absent / total) * 100

    if absent_pct >= 90:
        if already_flagged('mass_absent',
                           affected_section_id=section_id,
                           attendance_date=attendance_date):
            return

        anomaly = AttendanceAnomaly(
            anomaly_type='mass_absent',
            severity='high',
            title=f'👥 Mass Absence — Section {section_id}',
            description=f'{absent}/{total} students ({absent_pct:.0f}%) absent on {attendance_date}',
            ai_analysis='Entire section marked absent. This may indicate a cancelled class, data entry error, or a real event requiring investigation.',
            affected_section_id=section_id,
            affected_course_id=course_id,
            attendance_date=attendance_date,
            raw_data={
                'total': total,
                'absent': absent,
                'absent_pct': absent_pct
            }
        )
        db.session.add(anomaly)
        db.session.commit()


def run_all_checks(section_id=None, course_id=None, attendance_date=None):
    """Run all anomaly checks — call this after any attendance save."""
    if not attendance_date:
        attendance_date = date.today()

    try:
        if section_id and course_id:
            detect_speed_fraud(section_id, course_id, attendance_date)
            detect_mass_absent(section_id, course_id, attendance_date)

            students = Attendance.query.filter_by(
                section_id=section_id,
                course_id=course_id,
                date=attendance_date
            ).with_entities(Attendance.student_id).distinct().all()

            for (sid,) in students:
                detect_sudden_drop(sid, course_id)
    except Exception as e:
        print(f"Anomaly detection error: {e}")
