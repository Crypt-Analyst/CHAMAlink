from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.meeting_minutes import MeetingMinutes, ChamaAnnouncement
from app.models.chama import Chama
from app.models.user import User
from app import db
from datetime import datetime, date
import os
from werkzeug.utils import secure_filename

minutes_bp = Blueprint('minutes', __name__, url_prefix='/minutes')

@minutes_bp.route('/chama/<int:chama_id>')
@login_required
def chama_minutes(chama_id):
    """View all meeting minutes for a chama"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Check permissions
    if not current_user.is_member_of_chama(chama_id) and not current_user.is_super_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    minutes = MeetingMinutes.query.filter_by(chama_id=chama_id).order_by(
        MeetingMinutes.meeting_date.desc()
    ).all()
    
    user_role = current_user.get_chama_role(chama_id)
    can_create = user_role in ['secretary', 'admin', 'creator']
    
    return render_template('minutes/list.html', 
                         chama=chama, 
                         minutes=minutes, 
                         can_create=can_create,
                         user_role=user_role)

@minutes_bp.route('/create/<int:chama_id>')
@login_required
def create_minutes(chama_id):
    """Create new meeting minutes - Secretary/Admin only"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Check permissions
    user_role = current_user.get_chama_role(chama_id)
    if user_role not in ['secretary', 'admin', 'creator'] and not current_user.is_super_admin:
        flash('Only secretaries and admins can create meeting minutes.', 'error')
        return redirect(url_for('minutes.chama_minutes', chama_id=chama_id))
    
    # Get chama members for attendees selection
    members = chama.members
    
    return render_template('minutes/create.html', 
                         chama=chama, 
                         members=members)

@minutes_bp.route('/save/<int:chama_id>', methods=['POST'])
@login_required
def save_minutes(chama_id):
    """Save meeting minutes"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Check permissions
    user_role = current_user.get_chama_role(chama_id)
    if user_role not in ['secretary', 'admin', 'creator'] and not current_user.is_super_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        # Get form data
        meeting_date = datetime.strptime(request.form.get('meeting_date'), '%Y-%m-%d').date()
        meeting_title = request.form.get('meeting_title')
        attendees = request.form.getlist('attendees')  # List of member IDs
        agenda_items = request.form.get('agenda_items', '').split('\n')
        decisions_made = request.form.get('decisions_made')
        action_items = request.form.get('action_items', '').split('\n')
        minutes_content = request.form.get('minutes_content')
        
        # Handle file upload
        attachment_path = None
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename:
                filename = secure_filename(file.filename)
                upload_folder = os.path.join('app', 'static', 'uploads', 'minutes')
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, f"{chama_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}")
                file.save(file_path)
                attachment_path = file_path
        
        # Create minutes record
        minutes = MeetingMinutes(
            chama_id=chama_id,
            secretary_id=current_user.id,
            meeting_date=meeting_date,
            meeting_title=meeting_title,
            attendees=[int(id) for id in attendees if id],
            agenda_items=[item.strip() for item in agenda_items if item.strip()],
            decisions_made=decisions_made,
            action_items=[item.strip() for item in action_items if item.strip()],
            minutes_content=minutes_content,
            attachment_path=attachment_path,
            status='draft'
        )
        
        db.session.add(minutes)
        db.session.commit()
        
        flash('Meeting minutes saved successfully!', 'success')
        return redirect(url_for('minutes.view_minutes', minutes_id=minutes.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error saving minutes: {str(e)}', 'error')
        return redirect(url_for('minutes.create_minutes', chama_id=chama_id))

@minutes_bp.route('/view/<int:minutes_id>')
@login_required
def view_minutes(minutes_id):
    """View specific meeting minutes"""
    minutes = MeetingMinutes.query.get_or_404(minutes_id)
    
    # Check permissions
    if not current_user.is_member_of_chama(minutes.chama_id) and not current_user.is_super_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get attendee details
    attendees = []
    if minutes.attendees:
        attendees = User.query.filter(User.id.in_(minutes.attendees)).all()
    
    user_role = current_user.get_chama_role(minutes.chama_id)
    can_approve = user_role in ['admin', 'creator'] and minutes.status == 'draft'
    
    return render_template('minutes/view.html', 
                         minutes=minutes, 
                         attendees=attendees,
                         can_approve=can_approve,
                         user_role=user_role)

@minutes_bp.route('/approve/<int:minutes_id>', methods=['POST'])
@login_required
def approve_minutes(minutes_id):
    """Approve meeting minutes - Admin only"""
    minutes = MeetingMinutes.query.get_or_404(minutes_id)
    
    # Check permissions
    user_role = current_user.get_chama_role(minutes.chama_id)
    if user_role not in ['admin', 'creator'] and not current_user.is_super_admin:
        return jsonify({'success': False, 'message': 'Only admins can approve minutes'}), 403
    
    if minutes.status != 'draft':
        return jsonify({'success': False, 'message': 'Minutes already approved'}), 400
    
    try:
        minutes.status = 'approved'
        minutes.approved_by = current_user.id
        minutes.approved_at = datetime.utcnow()
        
        db.session.commit()
        
        # Create notification for all chama members about new approved minutes
        create_minutes_notification(minutes)
        
        flash('Meeting minutes approved and published!', 'success')
        return jsonify({'success': True, 'message': 'Minutes approved successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error approving minutes: {str(e)}'}), 500

def create_minutes_notification(minutes):
    """Create notification for all chama members about new minutes"""
    from app.models.chama import Notification
    
    for member in minutes.chama.members:
        notification = Notification(
            user_id=member.id,
            title=f"New Meeting Minutes: {minutes.meeting_title}",
            message=f"Meeting minutes from {minutes.meeting_date} have been approved and published.",
            type='minutes',
            related_id=minutes.id,
            chama_id=minutes.chama_id
        )
        db.session.add(notification)
    
    db.session.commit()
