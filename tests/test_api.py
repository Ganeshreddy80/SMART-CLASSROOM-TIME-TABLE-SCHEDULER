import pytest
import os
from models import Department, Course, Faculty, db
from tests.conftest import _FACULTY_PASS, _STUDENT_PASS, _ADMIN_PASS

def test_login_admin(client):
    res = client.post('/login', data={'email': 'admin@srmap.edu.in', 'password': _ADMIN_PASS}, follow_redirects=False)
    assert res.status_code == 302
    assert res.location == '/'

def test_login_faculty(client, seed_minimal):
    res = client.post('/login', data={'email': 'test.faculty@srmap.edu.in', 'password': _FACULTY_PASS}, follow_redirects=False)
    assert res.status_code == 302
    assert '/faculty-app' in res.location

def test_login_student(client, seed_minimal):
    res = client.post('/login', data={'email': 'test.student@srmap.edu.in', 'password': _STUDENT_PASS}, follow_redirects=False)
    assert res.status_code == 302
    assert '/student-app' in res.location

def test_get_departments(admin_session, seed_minimal):
    res = admin_session.get('/api/departments')
    assert res.status_code == 200
    data = res.get_json()
    # Filter out the admin department
    data = [d for d in data if d['code'] != 'ADM']
    assert len(data) == 1
    assert data[0]['code'] == 'CSE'

def test_add_course(admin_session, seed_minimal, app):
    with app.app_context():
        dept_id = Department.query.first().id

    res = admin_session.post('/api/courses', json={
        'code': 'NEW101',
        'name': 'New Course',
        'department_id': dept_id,
        'credits': 4,
        'difficulty': 'Hard',
        'course_type': 'Theory'
    })
    assert res.status_code == 201

    with app.app_context():
        course = Course.query.filter_by(code='NEW101').first()
        assert course is not None
        assert course.classes_per_week == 4

def test_delete_faculty(admin_session, seed_minimal, app):
    with app.app_context():
        fac_id = Faculty.query.first().id

    res = admin_session.delete(f'/api/faculty/{fac_id}')
    assert res.status_code == 200

    with app.app_context():
        fac = db.session.get(Faculty, fac_id)
        assert fac is None

def test_unauthorized_access(client):
    res = client.get('/api/departments')
    assert res.status_code == 401
