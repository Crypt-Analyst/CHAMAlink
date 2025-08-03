from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required

reconciliation_bp = Blueprint('reconciliation', __name__, url_prefix='/reconciliation')

@reconciliation_bp.route('/')
@login_required
def reconciliation_dashboard():
    """Automated reconciliation dashboard."""
    # TODO: Show reconciliation results
    return render_template('reconciliation/dashboard.html', results=[])

@reconciliation_bp.route('/api/check', methods=['POST'])
@login_required
def check_reconciliation():
    # TODO: Implement reconciliation logic
    return jsonify({'status': 'ok', 'message': 'Reconciliation complete.'})
