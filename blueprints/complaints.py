from flask import Blueprint, request, jsonify, session, render_template
from models import db, Complaint, Student, Faculty, Department
from blueprints.utils import login_required, role_required
from datetime import datetime
from sqlalchemy import func

complaints_bp = Blueprint('complaints_bp', __name__)

CATEGORY_ROUTING = {
    'infrastructure': ('Admin', 'admin'),
    'faculty_issue': ('HOD', 'hod'),
    'course_content': ('HOD', 'hod'),
    'hostel': ('Admin', 'admin'),
    'transport': ('Admin', 'admin'),
    'academic': ('HOD', 'hod'),
    'other': ('Admin', 'admin'),
}


@complaints_bp.route('/complaints')
@login_required
def complaints_page():
    return render_template('complaints.html')


@complaints_bp.route('/api/complaints', methods=['POST'])
@login_required
def submit_complaint():
    data = request.json or {}
    role = session.get('role')
    user_id = session.get('user_id')

    if role == 'student':
        user = Student.query.get(user_id)
        dept_id = user.department_id if user else None
        dept = Department.query.get(dept_id) if dept_id else None
        email = user.email if user else ''
    elif role == 'faculty':
        user = Faculty.query.get(user_id)
        dept_id = user.department_id if user else None
        dept = Department.query.get(dept_id) if dept_id else None
        email = user.email if user else ''
    else:
        return jsonify({'error': 'Unauthorized'}), 403

    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    if not title or not description:
        return jsonify({'error': 'Title and description are required'}), 400
    if len(description) < 20:
        return jsonify({'error': 'Description must be at least 20 characters'}), 400

    category = data.get('category', 'other')
    assigned_label, assigned_role = CATEGORY_ROUTING.get(category, ('Admin', 'admin'))

    if assigned_role == 'hod' and dept:
        assigned_to = f"HOD - {dept.name}"
    else:
        assigned_to = 'Admin'

    is_anonymous = data.get('is_anonymous', False)
    priority = data.get('priority', 'medium')

    year = datetime.utcnow().year
    max_id = db.session.query(func.max(Complaint.id)).scalar() or 0
    next_id = max_id + 1
    ticket_id = f"CMP-{year}-{next_id:04d}"

    complaint = Complaint(
        ticket_id=ticket_id,
        title=title,
        description=description,
        category=category,
        priority=priority,
        submitted_by_role=role,
        submitted_by_id=user_id,
        submitted_by_name=session.get('user_name', ''),
        submitted_by_email=email,
        department_id=dept_id,
        department_name=dept.name if dept else '',
        assigned_to=assigned_to,
        assigned_to_role=assigned_role,
        is_anonymous=is_anonymous,
        is_urgent=(priority == 'urgent'),
        status='open',
    )

    db.session.add(complaint)
    db.session.commit()
    complaint.generate_ticket_id()
    db.session.commit()

    return jsonify({
        'message': 'Complaint submitted successfully',
        'ticket_id': complaint.ticket_id,
        'complaint': complaint.to_dict(),
    }), 201


@complaints_bp.route('/api/complaints', methods=['GET'])
@login_required
def get_complaints():
    role = session.get('role')
    user_id = session.get('user_id')

    if role == 'admin':
        complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
    elif role in ['student', 'faculty']:
        complaints = Complaint.query.filter_by(
            submitted_by_id=user_id,
            submitted_by_role=role,
        ).order_by(Complaint.created_at.desc()).all()
    else:
        return jsonify([])

    return jsonify([c.to_dict() for c in complaints])


@complaints_bp.route('/api/complaints/<int:cid>/status', methods=['PUT'])
@login_required
@role_required('admin')
def update_complaint_status(cid):
    complaint = Complaint.query.get_or_404(cid)
    data = request.json or {}

    complaint.status = data.get('status', complaint.status)
    complaint.resolution_note = data.get('resolution_note', complaint.resolution_note)
    complaint.admin_remarks = data.get('admin_remarks', complaint.admin_remarks)
    complaint.updated_at = datetime.utcnow()

    if complaint.status in ['resolved', 'closed']:
        complaint.resolved_at = datetime.utcnow()

    db.session.commit()
    return jsonify({'message': 'Updated successfully', 'complaint': complaint.to_dict()})


@complaints_bp.route('/api/complaints/stats', methods=['GET'])
@login_required
@role_required('admin')
def complaint_stats():
    total = Complaint.query.count()
    open_count = Complaint.query.filter_by(status='open').count()
    in_progress = Complaint.query.filter_by(status='in_progress').count()
    resolved = Complaint.query.filter_by(status='resolved').count()
    urgent = Complaint.query.filter_by(is_urgent=True).count()

    return jsonify({
        'total': total,
        'open': open_count,
        'in_progress': in_progress,
        'resolved': resolved,
        'urgent': urgent,
    })


@complaints_bp.route('/api/complaints/analyze', methods=['POST'])
@login_required
def analyze_complaint():
    import requests, os
    data = request.json or {}
    text = data.get('text', '').strip()
    if len(text) < 20:
        return jsonify({'error': 'Too short'})

    prompt = f"""
    Analyze this university complaint and respond ONLY with JSON.
    Complaint: "{text}"

    Return exactly this JSON format, nothing else:
    {{
        "category": one of [infrastructure, faculty_issue, course_content, hostel, transport, academic, other],
        "priority": one of [low, medium, high, urgent],
        "summary": "one sentence summary under 15 words",
        "reason": "one sentence explaining why this category and priority"
    }}
    """

    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {os.environ.get("OPENROUTER_API_KEY","")}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'anthropic/claude-3-haiku',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 150
            },
            timeout=8
        )
        result = response.json()['choices'][0]['message']['content']
        import json, re
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            return jsonify(parsed)
    except Exception:
        pass

    return jsonify({'error': 'Analysis failed'})
