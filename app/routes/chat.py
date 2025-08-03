from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

@chat_bp.route('/')
@login_required
def chat_home():
    """In-app group chat UI."""
    # TODO: Integrate with real-time backend (e.g., Flask-SocketIO)
    return render_template('chat/home.html')

@chat_bp.route('/api/send', methods=['POST'])
@login_required
def send_message():
    data = request.json or {}
    # TODO: Save message to DB and broadcast
    return jsonify({'status': 'sent'})
