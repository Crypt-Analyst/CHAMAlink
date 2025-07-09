from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.chama import Chama, chama_members, Notification
from app.models.meeting_minutes import ChamaAnnouncement
from app.models.user import User
from app import db
from datetime import datetime, timedelta
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/chama/<int:chama_id>')
@login_required
def chama_admin(chama_id):
    """Admin dashboard for chama management"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Check permissions - only admin/creator can access
    user_role = current_user.get_chama_role(chama_id)
    if user_role not in ['admin', 'creator'] and not current_user.is_super_admin:
        flash('Access denied. Only admins can access this page.', 'error')
        return redirect(url_for('chama.detail', chama_id=chama_id))
    
    # Get recent announcements
    announcements = ChamaAnnouncement.query.filter_by(
        chama_id=chama_id, is_active=True
    ).order_by(ChamaAnnouncement.created_at.desc()).limit(5).all()
    
    # Get member statistics
    total_members = len(chama.members)
    pending_members = User.query.join(chama_members).filter(
        chama_members.c.chama_id == chama_id,
        chama_members.c.status == 'pending'
    ).count()
    
    return render_template('admin/dashboard.html',
                         chama=chama,
                         announcements=announcements,
                         total_members=total_members,
                         pending_members=pending_members,
                         user_role=user_role)

@admin_bp.route('/chama/<int:chama_id>/meeting', methods=['GET', 'POST'])
@login_required
def manage_meeting(chama_id):
    """Manage next meeting date"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Check permissions
    user_role = current_user.get_chama_role(chama_id)
    if user_role not in ['admin', 'creator'] and not current_user.is_super_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('chama.detail', chama_id=chama_id))
    
    if request.method == 'POST':
        try:
            # Get form data
            meeting_date = request.form.get('meeting_date')
            meeting_time = request.form.get('meeting_time')
            meeting_agenda = request.form.get('meeting_agenda', '')
            notify_members = request.form.get('notify_members') == 'on'
            
            # Parse and combine date and time
            if meeting_date and meeting_time:
                meeting_datetime = datetime.strptime(f"{meeting_date} {meeting_time}", '%Y-%m-%d %H:%M')
            else:
                meeting_datetime = datetime.strptime(meeting_date, '%Y-%m-%d')
            
            # Update chama
            chama.next_meeting_date = meeting_datetime
            db.session.commit()
            
            # Send notifications if requested
            if notify_members:
                send_meeting_notification(chama, meeting_datetime, meeting_agenda)
            
            flash('Next meeting date updated successfully!', 'success')
            return redirect(url_for('admin.chama_admin', chama_id=chama_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating meeting: {str(e)}', 'error')
    
    return render_template('admin/meeting.html', chama=chama, user_role=user_role)

@admin_bp.route('/chama/<int:chama_id>/announcements')
@login_required
def announcements(chama_id):
    """View and manage announcements"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Check permissions
    user_role = current_user.get_chama_role(chama_id)
    if user_role not in ['admin', 'creator'] and not current_user.is_super_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('chama.detail', chama_id=chama_id))
    
    # Get announcements
    announcements = ChamaAnnouncement.query.filter_by(chama_id=chama_id).order_by(
        ChamaAnnouncement.created_at.desc()
    ).all()
    
    return render_template('admin/announcements.html',
                         chama=chama,
                         announcements=announcements,
                         user_role=user_role)

@admin_bp.route('/chama/<int:chama_id>/announcement/create', methods=['GET', 'POST'])
@login_required
def create_announcement(chama_id):
    """Create new announcement"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Check permissions
    user_role = current_user.get_chama_role(chama_id)
    if user_role not in ['admin', 'creator'] and not current_user.is_super_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('chama.detail', chama_id=chama_id))
    
    if request.method == 'POST':
        try:
            # Get form data
            title = request.form.get('title')
            content = request.form.get('content')
            announcement_type = request.form.get('announcement_type', 'general')
            priority = request.form.get('priority', 'normal')
            target_members = request.form.getlist('target_members')
            expires_at = request.form.get('expires_at')
            send_notifications = request.form.get('send_notifications') == 'on'
            send_emails = request.form.get('send_emails') == 'on'
            
            # Parse expiry date
            expires_datetime = None
            if expires_at:
                expires_datetime = datetime.strptime(expires_at, '%Y-%m-%d')
            
            # Create announcement
            announcement = ChamaAnnouncement(
                chama_id=chama_id,
                admin_id=current_user.id,
                title=title,
                content=content,
                announcement_type=announcement_type,
                priority=priority,
                target_members=[int(id) for id in target_members if id] if target_members else None,
                expires_at=expires_datetime
            )
            
            db.session.add(announcement)
            db.session.commit()
            
            # Send notifications and emails
            if send_notifications or send_emails:
                send_announcement_notifications(announcement, send_notifications, send_emails)
            
            flash('Announcement created and sent successfully!', 'success')
            return redirect(url_for('admin.announcements', chama_id=chama_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating announcement: {str(e)}', 'error')
    
    # Get chama members for targeting
    members = chama.members
    
    return render_template('admin/announcement_create.html',
                         chama=chama,
                         members=members,
                         user_role=user_role)

@admin_bp.route('/announcement/<int:announcement_id>/toggle', methods=['POST'])
@login_required
def toggle_announcement(announcement_id):
    """Toggle announcement active status"""
    announcement = ChamaAnnouncement.query.get_or_404(announcement_id)
    
    # Check permissions
    user_role = current_user.get_chama_role(announcement.chama_id)
    if user_role not in ['admin', 'creator'] and not current_user.is_super_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        announcement.is_active = not announcement.is_active
        db.session.commit()
        
        status = 'activated' if announcement.is_active else 'deactivated'
        return jsonify({'success': True, 'message': f'Announcement {status}', 'is_active': announcement.is_active})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

def send_meeting_notification(chama, meeting_datetime, agenda=''):
    """Send meeting notification to all chama members"""
    from app.utils.email_utils import send_chama_email
    
    # Create notifications
    for member in chama.members:
        # In-app notification
        notification = Notification(
            user_id=member.id,
            title=f"Next Meeting Scheduled - {chama.name}",
            message=f"Next meeting scheduled for {meeting_datetime.strftime('%B %d, %Y at %I:%M %p')}",
            type='meeting',
            chama_id=chama.id
        )
        db.session.add(notification)
        
        # Email notification
        try:
            send_chama_email(
                to_email=member.email,
                subject=f"Next Meeting Scheduled - {chama.name}",
                template='emails/meeting_notification.html',
                chama=chama,
                member=member,
                meeting_datetime=meeting_datetime,
                agenda=agenda
            )
        except Exception as e:
            print(f"Failed to send email to {member.email}: {e}")
    
    db.session.commit()

def send_announcement_notifications(announcement, send_notifications=True, send_emails=True):
    """Send announcement notifications to targeted members"""
    from app.utils.email_utils import send_chama_email
    
    # Determine target members
    if announcement.target_members:
        target_users = User.query.filter(User.id.in_(announcement.target_members)).all()
    else:
        target_users = announcement.chama.members
    
    for user in target_users:
        # In-app notification
        if send_notifications:
            notification = Notification(
                user_id=user.id,
                title=f"{announcement.chama.name}: {announcement.title}",
                message=announcement.content[:200] + ('...' if len(announcement.content) > 200 else ''),
                type='announcement',
                related_id=announcement.id,
                chama_id=announcement.chama_id
            )
            db.session.add(notification)
        
        # Email notification
        if send_emails:
            try:
                send_chama_email(
                    to_email=user.email,
                    subject=f"{announcement.chama.name}: {announcement.title}",
                    template='emails/announcement.html',
                    chama=announcement.chama,
                    member=user,
                    announcement=announcement
                )
            except Exception as e:
                print(f"Failed to send email to {user.email}: {e}")
    
    db.session.commit()
