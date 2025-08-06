from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.user import User
from app.models.audit_log import AuditLog
from app import db

admin_analytics_bp = Blueprint('admin_analytics', __name__, url_prefix='/admin-analytics')

@admin_analytics_bp.route('/')
@login_required
def dashboard():
    if not (current_user.is_founder or current_user.role == 'it'):
        return '', 403
    user_count = User.query.count()
    admin_count = User.query.filter(User.role=='admin').count()
    it_count = User.query.filter(User.role=='it').count()
    audit_count = AuditLog.query.count()
    recent_audits = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()
    return render_template('admin_analytics/dashboard.html',
        user_count=user_count,
        admin_count=admin_count,
        it_count=it_count,
        audit_count=audit_count,
        recent_audits=recent_audits)
