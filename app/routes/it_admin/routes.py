from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.user import User
from app import db

def is_it_admin():
    # Allow IT, admin, super admin, or founder
    return (
        (hasattr(current_user, 'role') and current_user.role in ['it', 'admin'])
        or getattr(current_user, 'is_super_admin', False)
        or getattr(current_user, 'is_founder', False)
    )

it_admin_bp = Blueprint('it_admin', __name__, url_prefix='/it-admin')

@it_admin_bp.route('/')
@login_required
def dashboard():
    if not is_it_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))
    users = User.query.all()
    return render_template('it_admin/dashboard.html', users=users)

@it_admin_bp.route('/approve/<int:user_id>')
@login_required
def approve_user(user_id):
    if not is_it_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))
    user = User.query.get_or_404(user_id)
    user.is_active = True
    db.session.commit()
    # Log action
    from app.models.audit_log import AuditLog
    log = AuditLog(user_id=current_user.id, event='approve_user', details=f'Approved user {user.email}', ip_address=request.remote_addr)
    db.session.add(log)
    db.session.commit()
    flash(f'User {user.email} approved.', 'success')
    return redirect(url_for('it_admin.dashboard'))

@it_admin_bp.route('/suspend/<int:user_id>')
@login_required
def suspend_user(user_id):
    if not is_it_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))
    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()
    # Log action
    from app.models.audit_log import AuditLog
    log = AuditLog(user_id=current_user.id, event='suspend_user', details=f'Suspended user {user.email}', ip_address=request.remote_addr)
    db.session.add(log)
    db.session.commit()
    flash(f'User {user.email} suspended.', 'warning')
    return redirect(url_for('it_admin.dashboard'))

@it_admin_bp.route('/delete/<int:user_id>')
@login_required
def delete_user(user_id):
    if not is_it_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))
    user = User.query.get_or_404(user_id)
    # Delete related EmailVerification and UserSubscription records
    from app.models.subscription import EmailVerification, UserSubscription
    EmailVerification.query.filter_by(user_id=user.id).delete()
    UserSubscription.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    # Log action
    from app.models.audit_log import AuditLog
    log = AuditLog(user_id=current_user.id, event='delete_user', details=f'Deleted user {user.email}', ip_address=request.remote_addr)
    db.session.add(log)
    db.session.commit()
    flash(f'User {user.email} deleted.', 'danger')
    return redirect(url_for('it_admin.dashboard'))

@it_admin_bp.route('/logs')
@login_required
def view_logs():
    if not is_it_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))
    from app.models.audit_log import AuditLog, User
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(100).all()
    return render_template('it_admin/logs.html', logs=logs)
