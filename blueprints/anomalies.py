"""
anomalies.py — API routes for attendance anomaly management.
Admin-only endpoints to view, dismiss, and confirm anomalies.
"""
from flask import Blueprint, request, jsonify, session, render_template
from models import db, AttendanceAnomaly
from blueprints.utils import login_required, role_required
from datetime import datetime

anomalies_bp = Blueprint('anomalies_bp', __name__)


@anomalies_bp.route('/api/anomalies', methods=['GET'])
@login_required
@role_required('admin')
def get_anomalies():
    status = request.args.get('status', 'open')
    severity = request.args.get('severity')

    query = AttendanceAnomaly.query
    if status != 'all':
        query = query.filter_by(status=status)
    if severity:
        query = query.filter_by(severity=severity)

    anomalies = query.order_by(AttendanceAnomaly.date_detected.desc()).limit(100).all()
    return jsonify([a.to_dict() for a in anomalies])


@anomalies_bp.route('/api/anomalies/stats', methods=['GET'])
@login_required
@role_required('admin')
def anomaly_stats():
    return jsonify({
        'total': AttendanceAnomaly.query.filter_by(status='open').count(),
        'critical': AttendanceAnomaly.query.filter_by(status='open', severity='critical').count(),
        'high': AttendanceAnomaly.query.filter_by(status='open', severity='high').count(),
        'warning': AttendanceAnomaly.query.filter_by(status='open', severity='warning').count(),
    })


@anomalies_bp.route('/api/anomalies/<int:id>/dismiss', methods=['PUT'])
@login_required
@role_required('admin')
def dismiss_anomaly(id):
    anomaly = AttendanceAnomaly.query.get_or_404(id)
    data = request.json or {}
    anomaly.status = 'dismissed'
    anomaly.admin_note = data.get('note', '')
    anomaly.dismissed_by = session.get('user_name', 'Admin')
    anomaly.dismissed_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': 'Dismissed'})


@anomalies_bp.route('/anomalies')
@login_required
@role_required('admin')
def anomalies_page():
    return render_template('anomalies.html')


@anomalies_bp.route('/api/anomalies/<int:id>/confirm', methods=['PUT'])
@login_required
@role_required('admin')
def confirm_anomaly(id):
    anomaly = AttendanceAnomaly.query.get_or_404(id)
    data = request.json or {}
    anomaly.status = 'confirmed_fraud'
    anomaly.admin_note = data.get('note', '')
    db.session.commit()
    return jsonify({'message': 'Confirmed as fraud'})
