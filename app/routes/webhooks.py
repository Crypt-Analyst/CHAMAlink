from flask import Blueprint, request, jsonify
from flask_login import login_required

webhooks_bp = Blueprint('webhooks', __name__, url_prefix='/webhooks')

@webhooks_bp.route('/receive', methods=['POST'])
def receive_webhook():
    # TODO: Process incoming webhook
    data = request.json or {}
    return jsonify({'status': 'received', 'data': data})

@webhooks_bp.route('/test', methods=['GET'])
@login_required
def test_webhook():
    # TODO: Send a test webhook
    return jsonify({'status': 'test sent'})
