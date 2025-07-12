from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from app.models.meeting_minutes import MeetingMinutes, ChamaAnnouncement
from app.models.chama import Chama, chama_members
from app.models.user import User
from app import db
from datetime import datetime, date
import os
from werkzeug.utils import secure_filename
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

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

@minutes_bp.route('/<int:chama_id>/download-all')
@login_required
def download_all_minutes(chama_id):
    """Download all minutes as a combined PDF"""
    chama = Chama.query.get_or_404(chama_id)
    user_role = current_user.get_chama_role(chama_id)
    
    # Check permissions
    if not current_user.is_member_of_chama(chama_id) and not current_user.is_super_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get all minutes for this chama
    minutes_list = MeetingMinutes.query.filter_by(chama_id=chama_id).order_by(
        MeetingMinutes.meeting_date.desc()
    ).all()
    
    if not minutes_list:
        flash('No minutes found for this chama.', 'info')
        return redirect(url_for('minutes.chama_minutes', chama_id=chama_id))
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title page
    title = Paragraph(f"<b>All Meeting Minutes - {chama.name}</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 20))
    
    subtitle = Paragraph(f"<i>Generated on {datetime.now().strftime('%B %d, %Y')}</i>", styles['Normal'])
    elements.append(subtitle)
    elements.append(Spacer(1, 30))
    
    # Table of contents
    toc_title = Paragraph("<b>Table of Contents</b>", styles['Heading1'])
    elements.append(toc_title)
    elements.append(Spacer(1, 10))
    
    for i, minutes in enumerate(minutes_list, 1):
        toc_entry = Paragraph(f"{i}. {minutes.title} - {minutes.meeting_date.strftime('%B %d, %Y')}", styles['Normal'])
        elements.append(toc_entry)
    
    elements.append(PageBreak())
    
    # Add each minutes document
    for i, minutes in enumerate(minutes_list, 1):
        # Minutes header
        minutes_title = Paragraph(f"<b>{i}. {minutes.title}</b>", styles['Heading1'])
        elements.append(minutes_title)
        elements.append(Spacer(1, 10))
        
        # Meeting details
        details = f"<b>Date:</b> {minutes.meeting_date.strftime('%B %d, %Y')}<br/>"
        details += f"<b>Type:</b> {minutes.meeting_type.title()}<br/>"
        details += f"<b>Secretary:</b> {minutes.secretary.username}<br/>"
        if minutes.attendees:
            details += f"<b>Attendees:</b> {minutes.attendees}<br/>"
        
        details_para = Paragraph(details, styles['Normal'])
        elements.append(details_para)
        elements.append(Spacer(1, 20))
        
        # Content
        content_title = Paragraph("<b>Meeting Content:</b>", styles['Heading2'])
        elements.append(content_title)
        elements.append(Spacer(1, 10))
        
        # Split content into paragraphs
        content_lines = minutes.content.split('\n')
        for line in content_lines:
            if line.strip():
                content_para = Paragraph(line, styles['Normal'])
                elements.append(content_para)
        
        # Add page break between minutes (except for the last one)
        if i < len(minutes_list):
            elements.append(PageBreak())
    
    doc.build(elements)
    buffer.seek(0)
    
    filename = f"{chama.name}_all_minutes_{datetime.now().strftime('%Y%m%d')}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

@minutes_bp.route('/chama/<int:chama_id>/save', methods=['POST'])
@login_required
def save_minutes_action(chama_id):
    """Handle saving minutes as draft or sharing with members"""
    try:
        chama = Chama.query.get_or_404(chama_id)
        
        # Check if user is secretary or admin
        member = db.session.query(chama_members).filter(
            chama_members.c.chama_id == chama_id,
            chama_members.c.user_id == current_user.id
        ).first()
        
        if not member or member.role not in ['secretary', 'admin']:
            return jsonify({'success': False, 'message': 'Permission denied'}), 403
        
        data = request.get_json()
        action = data.get('action', 'save_draft')
        
        # Check if this is an edit or new minutes
        minutes_id = data.get('minutes_id')
        if minutes_id:
            minutes = MeetingMinutes.query.get_or_404(minutes_id)
        else:
            minutes = MeetingMinutes(
                chama_id=chama_id,
                secretary_id=current_user.id
            )
        
        # Update minutes data
        minutes.meeting_date = datetime.strptime(data.get('meeting_date'), '%Y-%m-%d').date()
        minutes.meeting_title = data.get('meeting_title', '')
        minutes.minutes_content = data.get('content', '')
        minutes.attendees = data.get('attendees', '').split(', ') if data.get('attendees') else []
        minutes.agenda_items = data.get('agenda_items', '').split('\n') if data.get('agenda_items') else []
        minutes.decisions_made = data.get('decisions_made', '')
        minutes.action_items = data.get('action_items', '').split('\n') if data.get('action_items') else []
        
        if action == 'share':
            minutes.status = 'shared'
            # Note: shared_at field doesn't exist in the model, using updated_at instead
            minutes.updated_at = datetime.utcnow()
        else:
            minutes.status = 'draft'
        
        db.session.add(minutes)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Minutes {"shared" if action == "share" else "saved as draft"} successfully',
            'minutes_id': minutes.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@minutes_bp.route('/chama/<int:chama_id>/download-temp', methods=['POST'])
@login_required
def download_temp_minutes(chama_id):
    """Download minutes without saving to database"""
    try:
        chama = Chama.query.get_or_404(chama_id)
        
        # Check permissions
        member = db.session.query(chama_members).filter(
            chama_members.c.chama_id == chama_id,
            chama_members.c.user_id == current_user.id
        ).first()
        
        if not member or member.role not in ['secretary', 'admin']:
            flash('Permission denied', 'error')
            return redirect(url_for('main.dashboard'))
        
        # Get form data
        meeting_date = request.form.get('meeting_date')
        meeting_title = request.form.get('meeting_title', 'Meeting Minutes')
        content = request.form.get('content', '')
        attendees = request.form.get('attendees', '')
        agenda_items = request.form.get('agenda_items', '')
        decisions_made = request.form.get('decisions_made', '')
        action_items = request.form.get('action_items', '')
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch)
        
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        story.append(Paragraph(f"{chama.name} - {meeting_title}", title_style))
        
        # Meeting details
        details_style = styles['Normal']
        story.append(Paragraph(f"<b>Date:</b> {meeting_date}", details_style))
        story.append(Paragraph(f"<b>Recorded by:</b> {current_user.username}", details_style))
        
        if attendees:
            story.append(Paragraph(f"<b>Attendees:</b> {attendees}", details_style))
        
        story.append(Spacer(1, 20))
        
        # Agenda Items
        if agenda_items:
            story.append(Paragraph("<b>Agenda Items:</b>", styles['Heading3']))
            agenda_list = agenda_items.split('\n')
            for item in agenda_list:
                if item.strip():
                    story.append(Paragraph(f"• {item.strip()}", details_style))
            story.append(Spacer(1, 15))
        
        # Content
        if content:
            story.append(Paragraph("<b>Meeting Minutes:</b>", styles['Heading3']))
            content_paragraphs = content.split('\n')
            for paragraph in content_paragraphs:
                if paragraph.strip():
                    story.append(Paragraph(paragraph, details_style))
                    story.append(Spacer(1, 10))
            story.append(Spacer(1, 15))
        
        # Decisions Made
        if decisions_made:
            story.append(Paragraph("<b>Key Decisions Made:</b>", styles['Heading3']))
            decisions_paragraphs = decisions_made.split('\n')
            for paragraph in decisions_paragraphs:
                if paragraph.strip():
                    story.append(Paragraph(paragraph, details_style))
                    story.append(Spacer(1, 10))
            story.append(Spacer(1, 15))
        
        # Action Items
        if action_items:
            story.append(Paragraph("<b>Action Items:</b>", styles['Heading3']))
            action_list = action_items.split('\n')
            for item in action_list:
                if item.strip():
                    story.append(Paragraph(f"• {item.strip()}", details_style))
            story.append(Spacer(1, 15))
        
        doc.build(story)
        
        # Return PDF
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"{chama.name}_{meeting_title}_{meeting_date}.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('minutes.create_minutes', chama_id=chama_id))
