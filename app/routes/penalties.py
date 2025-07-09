from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import (
    Chama, Penalty, Transaction, Notification, 
    MpesaTransaction, chama_members, User
)
from app.utils.permissions import chama_member_required, chama_admin_required, user_can_access_chama
from app.utils.mpesa import initiate_stk_push
from app import db
from datetime import datetime, timedelta
from sqlalchemy import desc, and_

penalties_bp = Blueprint('penalties', __name__, url_prefix='/penalties')

@penalties_bp.route('/')
@login_required
def penalty_dashboard():
    """Dashboard for penalties"""
    # Get user's penalties
    user_penalties = Penalty.query.filter_by(user_id=current_user.id).order_by(desc(Penalty.created_date)).all()
    
    # Get pending penalties for assignment (admin only)
    pending_assignments = []
    user_chamas = current_user.chamas
    
    for chama in user_chamas:
        # Check if user is admin in this chama
        user_role = db.session.query(chama_members.c.role).filter(
            and_(chama_members.c.user_id == current_user.id, 
                 chama_members.c.chama_id == chama.id)
        ).scalar()
        
        if user_role in ['admin', 'creator']:
            # Get all penalties for this chama (for admin oversight)
            chama_penalties = Penalty.query.filter_by(chama_id=chama.id).order_by(desc(Penalty.created_date)).all()
            pending_assignments.extend(chama_penalties)
    
    return render_template('penalties/dashboard.html',
                         user_penalties=user_penalties,
                         pending_assignments=pending_assignments)

@penalties_bp.route('/assign/<int:chama_id>')
@login_required
@chama_admin_required
def assign_penalty(chama_id):
    """Assign penalty form (admin only)"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Get chama members
    members = db.session.query(User, chama_members.c.role).join(
        chama_members, User.id == chama_members.c.user_id
    ).filter(chama_members.c.chama_id == chama_id).all()
    
    return render_template('penalties/assign.html', chama=chama, members=members)

@penalties_bp.route('/create_penalty', methods=['POST'])
@login_required
def create_penalty():
    """Create/assign penalty (admin only)"""
    try:
        data = request.get_json()
        chama_id = data.get('chama_id')
        user_id = data.get('user_id')
        penalty_type = data.get('type', '').strip()
        amount = float(data.get('amount', 0))
        description = data.get('description', '').strip()
        
        # Validation
        if not chama_id or not user_id or not penalty_type or not amount:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Amount must be greater than 0'}), 400
        
        # Security check - only admins can assign penalties
        user_role = db.session.query(chama_members.c.role).filter(
            and_(chama_members.c.user_id == current_user.id, 
                 chama_members.c.chama_id == chama_id)
        ).scalar()
        
        if user_role not in ['admin', 'creator']:
            return jsonify({'success': False, 'message': 'You do not have permission to assign penalties'}), 403
        
        # Check if user is member of chama
        member_check = db.session.query(chama_members.c.user_id).filter(
            and_(chama_members.c.user_id == user_id, 
                 chama_members.c.chama_id == chama_id)
        ).scalar()
        
        if not member_check:
            return jsonify({'success': False, 'message': 'User is not a member of this chama'}), 400
        
        # Create penalty
        penalty = Penalty(
            type=penalty_type,
            amount=amount,
            description=description,
            user_id=user_id,
            chama_id=chama_id
        )
        
        db.session.add(penalty)
        db.session.commit()
        
        # Notify user
        user = User.query.get(user_id)
        chama = Chama.query.get(chama_id)
        notification = Notification(
            title='Penalty Assigned',
            message=f'You have been assigned a penalty of {penalty.formatted_amount} for {penalty_type} in {chama.name}',
            type='penalty',
            user_id=user_id,
            chama_id=chama_id
        )
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Penalty assigned successfully!'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@penalties_bp.route('/pay/<int:penalty_id>', methods=['POST'])
@login_required
def pay_penalty(penalty_id):
    """Pay penalty via M-Pesa"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number', '').strip()
        
        penalty = Penalty.query.get_or_404(penalty_id)
        
        # Security check - only penalty owner can pay
        if penalty.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'You can only pay your own penalties'}), 403
        
        # Check if already paid
        if penalty.status == 'paid':
            return jsonify({'success': False, 'message': 'Penalty already paid'}), 400
        
        # Validate phone number
        if not phone_number:
            return jsonify({'success': False, 'message': 'Phone number is required'}), 400
        
        # Initiate M-Pesa payment
        mpesa_response = initiate_stk_push(
            phone_number=phone_number,
            amount=penalty.amount,
            account_reference=f"PENALTY-{penalty.id}",
            transaction_desc=f"Penalty payment - {penalty.type}"
        )
        
        if mpesa_response['success']:
            # Update penalty status
            penalty.status = 'paid'
            penalty.paid_date = datetime.utcnow()
            
            # Create transaction record
            transaction = Transaction(
                type='penalty_payment',
                amount=penalty.amount,
                description=f"Penalty payment - {penalty.type}",
                user_id=current_user.id,
                chama_id=penalty.chama_id
            )
            
            # Update chama balance
            chama = Chama.query.get(penalty.chama_id)
            chama.total_balance += penalty.amount
            
            # Create M-Pesa transaction record
            mpesa_transaction = MpesaTransaction(
                checkout_request_id=mpesa_response['checkout_request_id'],
                amount=penalty.amount,
                phone_number=phone_number,
                account_reference=f"PENALTY-{penalty.id}",
                transaction_desc=f"Penalty payment - {penalty.type}",
                user_id=current_user.id,
                chama_id=penalty.chama_id,
                transaction_id=transaction.id
            )
            
            db.session.add(transaction)
            db.session.add(mpesa_transaction)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Penalty payment initiated successfully! M-Pesa prompt sent.',
                'checkout_request_id': mpesa_response['checkout_request_id']
            })
        else:
            return jsonify({'success': False, 'message': mpesa_response['message']}), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@penalties_bp.route('/chama/<int:chama_id>')
@login_required
@chama_member_required
def chama_penalties(chama_id):
    """View penalties for a specific chama"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Get user's role in this chama
    user_role = db.session.query(chama_members.c.role).filter(
        and_(chama_members.c.user_id == current_user.id, 
             chama_members.c.chama_id == chama_id)
    ).scalar()
    
    # Regular members can only see their own penalties
    if user_role in ['admin', 'creator']:
        # Admins can see all penalties
        penalties = Penalty.query.filter_by(chama_id=chama_id).order_by(desc(Penalty.created_date)).all()
    else:
        # Members can only see their own penalties
        penalties = Penalty.query.filter_by(
            chama_id=chama_id, 
            user_id=current_user.id
        ).order_by(desc(Penalty.created_date)).all()
    
    return render_template('penalties/chama_penalties.html',
                         chama=chama,
                         penalties=penalties,
                         user_role=user_role)

@penalties_bp.route('/statistics/<int:chama_id>')
@login_required
@chama_admin_required
def penalty_statistics(chama_id):
    """View penalty statistics for admins"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Get penalty statistics
    total_penalties = Penalty.query.filter_by(chama_id=chama_id).count()
    paid_penalties = Penalty.query.filter_by(chama_id=chama_id, status='paid').count()
    pending_penalties = total_penalties - paid_penalties
    
    total_penalty_amount = db.session.query(db.func.sum(Penalty.amount)).filter_by(chama_id=chama_id).scalar() or 0
    paid_penalty_amount = db.session.query(db.func.sum(Penalty.amount)).filter_by(chama_id=chama_id, status='paid').scalar() or 0
    
    # Get penalty breakdown by type
    penalty_breakdown = db.session.query(
        Penalty.type,
        db.func.count(Penalty.id).label('count'),
        db.func.sum(Penalty.amount).label('total_amount')
    ).filter_by(chama_id=chama_id).group_by(Penalty.type).all()
    
    # Get recent penalties
    recent_penalties = Penalty.query.filter_by(chama_id=chama_id).order_by(desc(Penalty.created_date)).limit(10).all()
    
    return render_template('penalties/statistics.html',
                         chama=chama,
                         total_penalties=total_penalties,
                         paid_penalties=paid_penalties,
                         pending_penalties=pending_penalties,
                         total_penalty_amount=total_penalty_amount,
                         paid_penalty_amount=paid_penalty_amount,
                         penalty_breakdown=penalty_breakdown,
                         recent_penalties=recent_penalties)

def get_user_chama_role(user_id, chama_id):
    """Get user's role in a specific chama"""
    return db.session.query(chama_members.c.role).filter(
        and_(chama_members.c.user_id == user_id, 
             chama_members.c.chama_id == chama_id)
    ).scalar()
