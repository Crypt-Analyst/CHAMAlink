from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user

gamification_bp = Blueprint('gamification', __name__, url_prefix='/gamification')

@gamification_bp.route('/')
@login_required
def gamification_dashboard():
    """Gamification dashboard: leaderboards, badges, rewards."""
    # TODO: Query leaderboard and badges
    leaderboard = [
        {'name': 'Alice', 'points': 1200},
        {'name': 'Bob', 'points': 950},
        {'name': 'Carol', 'points': 800}
    ]
    badges = ['Early Bird', 'Top Saver', 'Referral Star']
    return render_template('gamification/dashboard.html', leaderboard=leaderboard, badges=badges)
