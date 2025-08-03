from flask import Blueprint, jsonify
from flask_login import login_required

health_bp = Blueprint('health', __name__, url_prefix='/health')

@health_bp.route('/')
@login_required
def health_check():
    """Basic health check endpoint."""
    return jsonify({'status': 'ok', 'message': 'CHAMAlink is healthy'})
