from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.chama import Chama, chama_members
from app.models.notification import Notification
from app import db
from datetime import datetime
from sqlalchemy import desc, and_

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

@notifications_bp.route('/')
@login_required
def notification_dashboard():
    """Dashboard for notifications"""
    # Get user's notifications
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(desc(Notification.created_date)).all()
    
    # Mark notifications as read if user views them
    unread_count = len([n for n in notifications if not n.is_read])
    
    return render_template('notifications/dashboard.html',
                         notifications=notifications,
                         unread_count=unread_count)

@notifications_bp.route('/mark_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_read(notification_id):
    """Mark notification as read"""
    notification = Notification.query.get_or_404(notification_id)
    
    # Security check
    if notification.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'success': True})

@notifications_bp.route('/mark_all_read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read"""
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    return jsonify({'success': True})

@notifications_bp.route('/count')
@login_required
def notification_count():
    """Get unread notification count"""
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})

@notifications_bp.route('/group')
@login_required
def group_announcements():
    """View group announcements and notifications"""
    # Get user's chama-related notifications
    notifications = Notification.query.filter_by(user_id=current_user.id).filter(
        Notification.chama_id.isnot(None)
    ).order_by(desc(Notification.created_date)).all()
    
    unread_count = len([n for n in notifications if not n.is_read])
    
    return render_template('notifications/group_announcements.html',
                         notifications=notifications,
                         unread_count=unread_count)

@notifications_bp.route('/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a specific notification as read"""
    notification = Notification.query.get_or_404(notification_id)
    
    # Security check
    if notification.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'success': True})

@notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read"""
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    return jsonify({'success': True})

@notifications_bp.route('/<int:notification_id>/delete', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    """Delete a notification"""
    notification = Notification.query.get_or_404(notification_id)
    
    # Security check
    if notification.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({'success': True})

def create_notification(user_id, title, message, notification_type, chama_id=None):
    """Utility function to create notifications"""
    notification = Notification(
        title=title,
        message=message,
        type=notification_type,
        user_id=user_id,
        chama_id=chama_id
    )
    db.session.add(notification)
    return notification

def create_meeting_reminder(chama_id, meeting_date):
    """Create meeting reminder notifications for all chama members"""
    chama = Chama.query.get(chama_id)
    if not chama:
        return
    
    # Get all members of the chama
    members = db.session.query(chama_members.c.user_id).filter(
        chama_members.c.chama_id == chama_id
    ).all()
    
    for member_id_tuple in members:
        member_id = member_id_tuple[0]
        create_notification(
            user_id=member_id,
            title=f'Meeting Reminder - {chama.name}',
            message=f'You have a meeting scheduled for {meeting_date.strftime("%A, %B %d, %Y")} at {chama.meeting_time or "TBD"}',
            notification_type='meeting',
            chama_id=chama_id
        )
    
    db.session.commit()

def create_bulk_notification(user_ids, title, message, notification_type, chama_id=None):
    """Create notifications for multiple users"""
    notifications = []
    for user_id in user_ids:
        notification = Notification(
            title=title,
            message=message,
            type=notification_type,
            user_id=user_id,
            chama_id=chama_id
        )
        notifications.append(notification)
    
    db.session.add_all(notifications)
    return notifications
