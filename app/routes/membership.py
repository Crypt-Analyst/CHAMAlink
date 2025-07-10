from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import (
    Chama, ChamaMembershipRequest, MembershipApproval, 
    Notification, chama_members, User
)
from app.utils.permissions import chama_member_required, chama_admin_required, user_can_access_chama
from app import db
from datetime import datetime
from sqlalchemy import desc, and_

membership_bp = Blueprint('membership', __name__, url_prefix='/membership')

@membership_bp.route('/requests')
@login_required
def membership_requests():
    """View membership requests"""
    # Get user's own membership requests
    user_requests = ChamaMembershipRequest.query.filter_by(user_id=current_user.id).order_by(desc(ChamaMembershipRequest.request_date)).all()
    
    # Get pending requests for approval if user is admin
    pending_approvals = []
    user_chamas = current_user.chamas
    
    for chama in user_chamas:
        # Check if user is admin in this chama
        user_role = db.session.query(chama_members.c.role).filter(
            and_(chama_members.c.user_id == current_user.id, 
                 chama_members.c.chama_id == chama.id)
        ).scalar()
        
        if user_role in ['admin', 'creator']:
            chama_requests = ChamaMembershipRequest.query.filter_by(
                chama_id=chama.id, 
                status='pending'
            ).all()
            pending_approvals.extend(chama_requests)
    
    return render_template('membership/requests.html',
                         user_requests=user_requests,
                         pending_approvals=pending_approvals)

@membership_bp.route('/leave/<int:chama_id>')
@login_required
@chama_member_required
def request_leave(chama_id):
    """Request to leave a chama"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Check if user is creator
    if chama.creator_id == current_user.id:
        flash('You cannot leave a chama you created. Please transfer ownership first.', 'error')
        return redirect(url_for('chama.chama_detail', chama_id=chama_id))
    
    # Check if user has pending leave request
    existing_request = ChamaMembershipRequest.query.filter_by(
        user_id=current_user.id,
        chama_id=chama_id,
        request_type='leave',
        status='pending'
    ).first()
    
    if existing_request:
        flash('You already have a pending leave request for this chama', 'warning')
        return redirect(url_for('membership.membership_requests'))
    
    return render_template('membership/leave_request.html', chama=chama)

@membership_bp.route('/submit_leave_request', methods=['POST'])
@login_required
def submit_leave_request():
    """Submit leave request"""
    try:
        data = request.get_json()
        chama_id = data.get('chama_id')
        reason = data.get('reason', '').strip()
        
        # Validation
        if not chama_id:
            return jsonify({'success': False, 'message': 'Chama ID is required'}), 400
        
        # Security check
        if not user_can_access_chama(current_user.id, chama_id):
            return jsonify({'success': False, 'message': 'You are not a member of this chama'}), 403
        
        # Check if user is creator
        chama = Chama.query.get(chama_id)
        if chama.creator_id == current_user.id:
            return jsonify({'success': False, 'message': 'You cannot leave a chama you created'}), 400
        
        # Check for existing pending request
        existing_request = ChamaMembershipRequest.query.filter_by(
            user_id=current_user.id,
            chama_id=chama_id,
            request_type='leave',
            status='pending'
        ).first()
        
        if existing_request:
            return jsonify({'success': False, 'message': 'You already have a pending leave request'}), 400
        
        # Create leave request
        leave_request = ChamaMembershipRequest(
            user_id=current_user.id,
            chama_id=chama_id,
            request_type='leave',
            reason=reason
        )
        
        db.session.add(leave_request)
        db.session.commit()
        
        # Notify admins
        create_membership_notification(leave_request)
        
        return jsonify({'success': True, 'message': 'Leave request submitted successfully!'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@membership_bp.route('/approve/<int:request_id>', methods=['POST'])
@login_required
def approve_request(request_id):
    """Approve a membership request"""
    try:
        membership_request = ChamaMembershipRequest.query.get_or_404(request_id)
        
        # Check if user is admin of the chama
        user_role = get_user_chama_role(current_user.id, membership_request.chama_id)
        if user_role not in ['admin', 'creator']:
            return jsonify({'success': False, 'message': 'You do not have permission to approve this request'}), 403
        
        # Update request status
        membership_request.status = 'approved'
        membership_request.approval_date = datetime.utcnow()
        
        # Add user to chama if it's a join request
        if membership_request.request_type == 'join':
            chama = Chama.query.get(membership_request.chama_id)
            user = User.query.get(membership_request.user_id)
            
            # Check if user is already a member
            if user not in chama.members:
                chama.members.append(user)
        
        # Create approval record
        approval = MembershipApproval(
            request_id=request_id,
            approved_by=current_user.id,
            approval_date=datetime.utcnow(),
            status='approved'
        )
        db.session.add(approval)
        
        # Create notification for the requester
        notification = Notification(
            title='Membership Request Approved',
            message=f'Your request to join {membership_request.chama.name} has been approved',
            type='membership',
            user_id=membership_request.user_id,
            chama_id=membership_request.chama_id
        )
        db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Request approved successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@membership_bp.route('/reject/<int:request_id>', methods=['POST'])
@login_required
def reject_request(request_id):
    """Reject a membership request"""
    try:
        membership_request = ChamaMembershipRequest.query.get_or_404(request_id)
        
        # Check if user is admin of the chama
        user_role = get_user_chama_role(current_user.id, membership_request.chama_id)
        if user_role not in ['admin', 'creator']:
            return jsonify({'success': False, 'message': 'You do not have permission to reject this request'}), 403
        
        # Get rejection reason from request data
        data = request.get_json() or {}
        reason = data.get('reason', '')
        
        # Update request status
        membership_request.status = 'rejected'
        membership_request.rejection_reason = reason
        
        # Create approval record (with rejected status)
        approval = MembershipApproval(
            request_id=request_id,
            approved_by=current_user.id,
            approval_date=datetime.utcnow(),
            status='rejected',
            notes=reason
        )
        db.session.add(approval)
        
        # Create notification for the requester
        notification_message = f'Your request to join {membership_request.chama.name} has been rejected'
        if reason:
            notification_message += f': {reason}'
            
        notification = Notification(
            title='Membership Request Rejected',
            message=notification_message,
            type='membership',
            user_id=membership_request.user_id,
            chama_id=membership_request.chama_id
        )
        db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Request rejected successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@membership_bp.route('/cancel/<int:request_id>', methods=['POST'])
@login_required
def cancel_request(request_id):
    """Cancel a membership request"""
    try:
        membership_request = ChamaMembershipRequest.query.get_or_404(request_id)
        
        # Check if user owns this request
        if membership_request.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'You can only cancel your own requests'}), 403
        
        # Check if request is still pending
        if membership_request.status != 'pending':
            return jsonify({'success': False, 'message': 'Only pending requests can be canceled'}), 400
        
        # Update request status
        membership_request.status = 'canceled'
        
        # Create notification for chama admins
        chama = Chama.query.get(membership_request.chama_id)
        admin_ids = db.session.query(chama_members.c.user_id).filter(
            and_(chama_members.c.chama_id == chama.id,
                 chama_members.c.role.in_(['admin', 'creator']))
        ).all()
        
        for admin_id_tuple in admin_ids:
            admin_id = admin_id_tuple[0]
            notification = Notification(
                title='Membership Request Canceled',
                message=f'{current_user.username} has canceled their request to join {chama.name}',
                type='membership',
                user_id=admin_id,
                chama_id=chama.id
            )
            db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Request canceled successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@membership_bp.route('/join/<int:chama_id>')
@login_required
def request_join(chama_id):
    """Request to join a chama"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Check if user is already a member
    if current_user in chama.members:
        flash('You are already a member of this chama', 'warning')
        return redirect(url_for('chama.chama_detail', chama_id=chama_id))
    
    # Check if user has pending join request
    existing_request = ChamaMembershipRequest.query.filter_by(
        user_id=current_user.id,
        chama_id=chama_id,
        request_type='join',
        status='pending'
    ).first()
    
    if existing_request:
        flash('You already have a pending join request for this chama', 'warning')
        return redirect(url_for('membership.membership_requests'))
    
    return render_template('membership/join_request.html', chama=chama)

@membership_bp.route('/submit_join_request', methods=['POST'])
@login_required
def submit_join_request():
    """Submit join request"""
    try:
        data = request.get_json()
        chama_id = data.get('chama_id')
        reason = data.get('reason', '').strip()
        
        # Validation
        if not chama_id:
            return jsonify({'success': False, 'message': 'Chama ID is required'}), 400
        
        chama = Chama.query.get(chama_id)
        if not chama:
            return jsonify({'success': False, 'message': 'Chama not found'}), 404
        
        # Check if user is already a member
        if current_user in chama.members:
            return jsonify({'success': False, 'message': 'You are already a member of this chama'}), 400
        
        # Check for existing pending request
        existing_request = ChamaMembershipRequest.query.filter_by(
            user_id=current_user.id,
            chama_id=chama_id,
            request_type='join',
            status='pending'
        ).first()
        
        if existing_request:
            return jsonify({'success': False, 'message': 'You already have a pending join request'}), 400
        
        # Create join request
        join_request = ChamaMembershipRequest(
            user_id=current_user.id,
            chama_id=chama_id,
            request_type='join',
            reason=reason
        )
        
        db.session.add(join_request)
        db.session.commit()
        
        # Notify admins
        create_membership_notification(join_request)
        
        return jsonify({'success': True, 'message': 'Join request submitted successfully!'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

def create_membership_notification(membership_request):
    """Create notifications for admins about membership request"""
    chama = Chama.query.get(membership_request.chama_id)
    
    # Get all admins for this chama
    admins = db.session.query(chama_members.c.user_id).filter(
        and_(chama_members.c.chama_id == membership_request.chama_id,
             chama_members.c.role.in_(['admin', 'creator']))
    ).all()
    
    request_type = membership_request.request_type.title()
    
    for admin_id_tuple in admins:
        admin_id = admin_id_tuple[0]
        notification = Notification(
            title=f'New {request_type} Request',
            message=f'{membership_request.user.username} has requested to {membership_request.request_type} {chama.name}',
            type='membership',
            user_id=admin_id,
            chama_id=membership_request.chama_id
        )
        db.session.add(notification)

def get_user_chama_role(user_id, chama_id):
    """Get user's role in a specific chama"""
    return db.session.query(chama_members.c.role).filter(
        and_(chama_members.c.user_id == user_id, 
             chama_members.c.chama_id == chama_id)
    ).scalar()
