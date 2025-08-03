from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required

fraud_detection_bp = Blueprint('fraud_detection', __name__, url_prefix='/fraud')

@fraud_detection_bp.route('/')
@login_required
def fraud_dashboard():
    """Fraud detection dashboard."""
    # TODO: Show fraud alerts
    return render_template('fraud/dashboard.html', alerts=[])

@fraud_detection_bp.route('/api/scan', methods=['POST'])
@login_required
def scan_fraud():
    # TODO: Implement fraud detection logic
    return jsonify({'status': 'ok', 'message': 'No fraud detected.'})
