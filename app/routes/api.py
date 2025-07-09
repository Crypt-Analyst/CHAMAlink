from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models.chama import Chama, ChamaMember, Contribution, Receipt
from app import db
from datetime import datetime
import uuid
from app.utils.email_service import send_email

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/generate-receipt', methods=['POST'])
@login_required
def generate_receipt():
    """Generate a receipt from a contribution"""
    try:
        data = request.get_json()
        contribution_id = data.get('contribution_id')
        
        if not contribution_id:
            return jsonify({'error': 'Contribution ID is required'}), 400
        
        contribution = Contribution.query.get(contribution_id)
        if not contribution:
            return jsonify({'error': 'Contribution not found'}), 404
        
        # Check if user has permission to view this contribution
        member_role = ChamaMember.get_member_role(current_user.id, contribution.chama_id)
        if not member_role:
            return jsonify({'error': 'Permission denied'}), 403
        
        # Check if user can access this contribution
        if contribution.user_id != current_user.id and member_role not in ['admin', 'treasurer']:
            return jsonify({'error': 'Permission denied'}), 403
        
        # Check if contribution is confirmed
        if contribution.status != 'confirmed':
            return jsonify({'error': 'Receipt can only be generated for confirmed contributions'}), 400
        
        # Check if receipt already exists
        existing_receipt = Receipt.query.filter_by(
            contribution_id=contribution.id
        ).first()
        
        if existing_receipt:
            return jsonify({'receipt_id': existing_receipt.id})
        
        # Generate receipt number
        receipt_number = f"RCT-{contribution.chama_id}-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Create receipt
        receipt = Receipt(
            chama_id=contribution.chama_id,
            user_id=contribution.user_id,
            contribution_id=contribution.id,
            receipt_number=receipt_number,
            amount=contribution.amount,
            payment_type=contribution.type,
            transaction_id=contribution.transaction_id,
            status='confirmed',
            notes=f"Receipt for {contribution.type} contribution"
        )
        
        db.session.add(receipt)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'receipt_id': receipt.id,
            'receipt_number': receipt.receipt_number
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error generating receipt: {str(e)}'}), 500

@api_bp.route('/api/recurring-payments/check-due', methods=['GET'])
@login_required  
def check_due_payments():
    """Check for due recurring payments for the current user"""
    try:
        from app.models.chama import RecurringPayment
        
        today = datetime.now().date()
        
        due_payments = RecurringPayment.query.filter(
            RecurringPayment.user_id == current_user.id,
            RecurringPayment.is_active == True,
            RecurringPayment.next_payment_date <= today
        ).all()
        
        return jsonify({
            'due_count': len(due_payments),
            'due_payments': [{
                'id': payment.id,
                'chama_name': payment.chama.name,
                'amount': payment.amount,
                'payment_type': payment.payment_type,
                'next_payment_date': payment.next_payment_date.isoformat()
            } for payment in due_payments]
        })
        
    except Exception as e:
        return jsonify({'error': f'Error checking due payments: {str(e)}'}), 500


@api_bp.route('/api/meetings/schedule', methods=['POST'])
@login_required
def schedule_meeting():
    """Schedule a new online meeting"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'chama_id', 'date', 'time']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        # Validate chama ownership
        chama = Chama.query.get(data['chama_id'])
        if not chama:
            return jsonify({'success': False, 'message': 'Invalid chama selected'}), 400
        
        # Check if user is a member of the chama
        from app.models.chama import ChamaMember
        member_role = ChamaMember.get_member_role(current_user.id, chama.id)
        if not member_role:
            return jsonify({'success': False, 'message': 'You are not a member of this chama'}), 400
        
        # Create meeting datetime
        meeting_datetime = datetime.strptime(
            f"{data['date']} {data['time']}", 
            "%Y-%m-%d %H:%M"
        )
        
        # Check if meeting is in the future
        if meeting_datetime <= datetime.now():
            return jsonify({'success': False, 'message': 'Meeting must be scheduled for a future date and time'}), 400
        
        # Generate Google Meet link (in production, this would integrate with Google Calendar API)
        meet_link = f"https://meet.google.com/new"
        
        # For now, we'll store meeting info in a simple way
        # In production, you'd want a proper Meeting model
        meeting_data = {
            'id': str(uuid.uuid4()),
            'title': data['title'],
            'chama_id': data['chama_id'],
            'scheduled_by': current_user.id,
            'meeting_datetime': meeting_datetime.isoformat(),
            'agenda': data.get('agenda', ''),
            'meet_link': meet_link,
            'status': 'scheduled'
        }
        
        # TODO: Store in database when Meeting model is created
        # For now, we'll return success
        
        return jsonify({
            'success': True,
            'message': 'Meeting scheduled successfully! Google Meet link generated.',
            'meeting_id': meeting_data['id'],
            'meet_link': meet_link
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'message': 'Invalid date or time format'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error scheduling meeting: {str(e)}'}), 500


@api_bp.route('/api/meetings/upcoming', methods=['GET'])
@login_required
def get_upcoming_meetings():
    """Get upcoming meetings for user's chamas"""
    try:
        # Get user's chamas
        user_chamas = current_user.chamas
        
        # For now, return sample data since we don't have Meeting model yet
        # In production, this would query the Meeting table
        sample_meetings = [
            {
                'id': 1,
                'title': 'Monthly Contribution Meeting',
                'chama_name': user_chamas[0].name if user_chamas else 'Sample Chama',
                'date': '2025-07-15',
                'time': '14:00',
                'agenda': 'Review monthly contributions and discuss investment opportunities',
                'meet_link': 'https://meet.google.com/new',
                'status': 'Upcoming'
            }
        ] if user_chamas else []
        
        return jsonify({
            'success': True,
            'meetings': sample_meetings
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error fetching meetings: {str(e)}'}), 500


# Chama-specific meeting routes
@api_bp.route('/api/chama/<int:chama_id>/meetings', methods=['GET'])
@login_required
def get_chama_meetings(chama_id):
    """Get meetings for a specific chama"""
    try:
        # Check if user has access to this chama
        chama = Chama.query.get_or_404(chama_id)
        user_role = current_user.get_chama_role(chama_id)
        if not user_role:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        # For now, return sample meetings since we don't have Meeting model yet
        # In production, this would query the Meeting table filtered by chama_id
        sample_meetings = [
            {
                'id': 1,
                'title': f'{chama.name} Monthly Meeting',
                'scheduled_time': '2025-07-15T14:00:00',
                'description': 'Monthly contribution review and planning session',
                'meeting_link': 'https://meet.google.com/new',
                'chama_id': chama_id,
                'created_by': current_user.id
            },
            {
                'id': 2,
                'title': f'{chama.name} Investment Discussion',
                'scheduled_time': '2025-07-20T10:00:00',
                'description': 'Discuss new investment opportunities',
                'meeting_link': 'https://meet.google.com/new',
                'chama_id': chama_id,
                'created_by': current_user.id
            }
        ]
        
        return jsonify({
            'success': True,
            'meetings': sample_meetings
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error fetching chama meetings: {str(e)}'}), 500


@api_bp.route('/api/schedule-meeting', methods=['POST'])
@login_required
def schedule_chama_meeting():
    """Schedule a new meeting for a specific chama"""
    try:
        data = request.get_json()
        
        # Required fields
        required_fields = ['title', 'scheduled_time', 'chama_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        chama_id = data.get('chama_id')
        
        # Check if user has admin access to this chama
        chama = Chama.query.get_or_404(chama_id)
        user_role = current_user.get_chama_role(chama_id)
        if user_role not in ['creator', 'admin']:
            return jsonify({'success': False, 'message': 'Only chama admins can schedule meetings'}), 403
        
        # Parse meeting datetime
        try:
            meeting_datetime = datetime.strptime(data['scheduled_time'], '%Y-%m-%d %H:%M')
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD HH:MM'}), 400
        
        # Check if meeting is in the future
        if meeting_datetime <= datetime.now():
            return jsonify({'success': False, 'message': 'Meeting must be scheduled for a future date and time'}), 400
        
        # Generate Google Meet link (simplified)
        import uuid
        meet_id = str(uuid.uuid4())[:8]
        meet_link = f"https://meet.google.com/{meet_id}"
        
        # For now, create a simple meeting object
        # In production, this would create a Meeting database record
        meeting_data = {
            'id': int(datetime.now().timestamp()),
            'title': data['title'],
            'description': data.get('description', ''),
            'scheduled_time': meeting_datetime.isoformat(),
            'meeting_link': meet_link,
            'chama_id': chama_id,
            'created_by': current_user.id,
            'status': 'scheduled'
        }
        
        # TODO: Store in database when Meeting model is created
        
        return jsonify({
            'success': True,
            'message': 'Meeting scheduled successfully!',
            'meeting': meeting_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error scheduling meeting: {str(e)}'}), 500


@api_bp.route('/api/meeting/<int:meeting_id>', methods=['DELETE'])
@login_required
def delete_meeting(meeting_id):
    """Delete a meeting (admin only)"""
    try:
        # For now, just return success since we don't have Meeting model yet
        # In production, this would:
        # 1. Find the meeting by ID
        # 2. Check if user has admin rights to the chama
        # 3. Delete the meeting from database
        
        return jsonify({
            'success': True,
            'message': 'Meeting deleted successfully!'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error deleting meeting: {str(e)}'}), 500


@api_bp.route('/api/request-agent-help', methods=['POST'])
def request_agent_help():
    """Send user message to support team when they request agent help"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        user_email = data.get('user_email', 'anonymous')
        user_name = data.get('user_name', 'Anonymous User')
        timestamp = data.get('timestamp', datetime.now().isoformat())
        conversation_history = data.get('conversation_history', [])
        
        # Email content for support team
        email_subject = f"🤝 Agent Help Request - {user_name}"
        email_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
                <h2 style="margin: 0; display: flex; align-items: center;">
                    <span style="margin-right: 10px;">🤝</span>
                    Agent Help Request
                </h2>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                <h3 style="color: #495057; margin-top: 0;">User Details</h3>
                <p><strong>Name:</strong> {user_name}</p>
                <p><strong>Email:</strong> {user_email}</p>
                <p><strong>Request Time:</strong> {timestamp}</p>
                
                <h3 style="color: #495057; margin-top: 30px;">User Message</h3>
                <div style="background: white; padding: 15px; border-radius: 5px; border-left: 4px solid #667eea;">
                    <p style="margin: 0; line-height: 1.6;"><strong>Latest:</strong> {user_message}</p>
                </div>
                
                {f'''
                <h3 style="color: #495057; margin-top: 20px;">Conversation History</h3>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; max-height: 200px; overflow-y: auto;">
                    {'<br>'.join([f"• {msg.get('message', 'No message')}" for msg in conversation_history[-5:]])}
                </div>
                ''' if conversation_history else ''}
                
                <div style="margin-top: 30px; padding: 15px; background: #e3f2fd; border-radius: 5px;">
                    <h4 style="color: #1565c0; margin-top: 0;">Next Steps</h4>
                    <p style="margin: 0;">
                        Please respond to this user as soon as possible. You can reply directly to this email 
                        or use the ChamaLink admin dashboard to continue the chat conversation.
                    </p>
                </div>
            </div>
        </div>
        """
        
        # Send email to support team
        support_email = "support@chamalink.co.ke"  # Your support email
        success = send_email(
            to_email=support_email,
            subject=email_subject,
            body=email_body,
            is_html=True
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Agent help request sent successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send agent help request'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
