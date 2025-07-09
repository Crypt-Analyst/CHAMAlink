from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import Chama, Transaction, Event, User, chama_members, RegistrationFeePayment, ChamaMembershipRequest, Notification, ManualPaymentVerification
from app.utils.permissions import chama_member_required, chama_admin_required, user_can_access_chama
from app import db
from datetime import datetime, date
from sqlalchemy import desc
from app.utils.mpesa import initiate_stk_push

chama_bp = Blueprint('chama', __name__, url_prefix='/chama')

@chama_bp.route('/<int:chama_id>')
@login_required
@chama_member_required
def chama_detail(chama_id):
    """View detailed information about a specific chama"""
    # Check subscription status (bypass for super admins)
    if not current_user.is_super_admin:
        from app.utils.subscription_utils import check_trial_expiry
        subscription = current_user.current_subscription
        
        if not subscription or not subscription.is_active:
            flash('Your subscription has expired. Please upgrade to access your chama.', 'danger')
            return redirect(url_for('subscription.plans'))
    
    chama = Chama.query.get_or_404(chama_id)
    
    # Get chama statistics
    total_contributions = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.chama_id == chama_id,
        Transaction.type == 'contribution'
    ).scalar() or 0
    
    total_loans = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.chama_id == chama_id,
        Transaction.type == 'loan'
    ).scalar() or 0
    
    # Get recent transactions for this chama
    recent_transactions = Transaction.query.filter(
        Transaction.chama_id == chama_id
    ).order_by(desc(Transaction.created_at)).limit(10).all()
    
    # Get upcoming events for this chama
    upcoming_events = Event.query.filter(
        Event.chama_id == chama_id,
        Event.event_date >= date.today()
    ).order_by(Event.event_date).limit(5).all()
    
    # Get user's role in this chama
    user_role = get_user_chama_role(current_user.id, chama_id)
    
    return render_template('chama/detail.html',
                         chama=chama,
                         total_contributions=total_contributions,
                         total_loans=total_loans,
                         recent_transactions=recent_transactions,
                         upcoming_events=upcoming_events,
                         user_role=user_role)

@chama_bp.route('/<int:chama_id>/members')
@login_required
@chama_member_required
def chama_members(chama_id):
    """View chama members (only accessible to chama members)"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Get members with their roles
    members_with_roles = db.session.query(
        User, chama_members.c.role, chama_members.c.joined_at
    ).join(chama_members, User.id == chama_members.c.user_id).filter(
        chama_members.c.chama_id == chama_id
    ).all()
    
    user_role = get_user_chama_role(current_user.id, chama_id)
    
    return render_template('chama/members.html',
                         chama=chama,
                         members_with_roles=members_with_roles,
                         user_role=user_role)

@chama_bp.route('/<int:chama_id>/contribute', methods=['POST'])
@login_required
@chama_member_required
def contribute(chama_id):
    """Make a contribution to a chama"""
    try:
        data = request.get_json()
        amount = float(data.get('amount', 0))
        
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Amount must be greater than 0'}), 400
        
        # Create transaction
        transaction = Transaction(
            type='contribution',
            amount=amount,
            description=f"Contribution to {Chama.query.get(chama_id).name}",
            user_id=current_user.id,
            chama_id=chama_id
        )
        
        db.session.add(transaction)
        
        # Update chama balance
        chama = Chama.query.get(chama_id)
        chama.total_balance += amount
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Contribution successful!'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@chama_bp.route('/<int:chama_id>/invite', methods=['POST'])
@login_required
@chama_admin_required
def invite_member(chama_id):
    """Invite a new member to the chama (admin only)"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'message': 'Email is required'}), 400
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Check if user is already a member
        chama = Chama.query.get(chama_id)
        if user in chama.members:
            return jsonify({'success': False, 'message': 'User is already a member'}), 400
        
        # Add user to chama
        chama.members.append(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'{user.username} has been added to the chama!'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@chama_bp.route('/<int:chama_id>/remove_member', methods=['POST'])
@login_required
@chama_admin_required
def remove_member(chama_id):
    """Remove a member from the chama (admin only)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': 'User ID is required'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        chama = Chama.query.get(chama_id)
        if user not in chama.members:
            return jsonify({'success': False, 'message': 'User is not a member'}), 400
        
        # Cannot remove the creator
        if user.id == chama.creator_id:
            return jsonify({'success': False, 'message': 'Cannot remove the chama creator'}), 400
        
        # Remove user from chama
        chama.members.remove(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'{user.username} has been removed from the chama!'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@chama_bp.route('/<int:chama_id>/transactions')
@login_required
@chama_member_required
def chama_transactions(chama_id):
    """View all transactions for a chama"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get transactions with pagination
    transactions = Transaction.query.filter(
        Transaction.chama_id == chama_id
    ).order_by(desc(Transaction.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('chama/transactions.html',
                         chama=chama,
                         transactions=transactions)

@chama_bp.route('/<int:chama_id>/pay-registration-fee', methods=['POST'])
@login_required
@chama_member_required
def pay_registration_fee(chama_id):
    """Pay registration fee for a chama"""
    try:
        data = request.get_json()
        phone = data.get('phone')
        
        if not phone:
            return jsonify({'success': False, 'message': 'Phone number is required'}), 400
        
        chama = Chama.query.get_or_404(chama_id)
        
        if chama.registration_fee <= 0:
            return jsonify({'success': False, 'message': 'No registration fee required for this chama'}), 400
        
        # Check if user has already paid registration fee
        existing_payment = RegistrationFeePayment.query.filter(
            RegistrationFeePayment.user_id == current_user.id,
            RegistrationFeePayment.chama_id == chama_id,
            RegistrationFeePayment.payment_status == 'completed'
        ).first()
        
        if existing_payment:
            return jsonify({'success': False, 'message': 'Registration fee already paid'}), 400
        
        # Create payment record
        payment = RegistrationFeePayment(
            user_id=current_user.id,
            chama_id=chama_id,
            amount=chama.registration_fee,
            payment_status='pending'
        )
        
        db.session.add(payment)
        db.session.commit()
        
        # Initiate M-Pesa STK push
        response = initiate_stk_push(
            phone_number=phone,
            amount=chama.registration_fee,
            account_reference=f"REG-{chama.id}-{current_user.id}",
            transaction_desc=f"Registration fee for {chama.name}"
        )
        
        if response.get('success'):
            return jsonify({
                'success': True,
                'message': 'Registration fee payment initiated. Please complete the payment on your phone.',
                'checkout_request_id': response.get('checkout_request_id')
            })
        else:
            # Update payment status to failed
            payment.payment_status = 'failed'
            db.session.commit()
            return jsonify({'success': False, 'message': 'Failed to initiate payment'}), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@chama_bp.route('/search')
@login_required
def search_chamas():
    """Search for chamas to join"""
    query = request.args.get('q', '')
    chamas = []
    
    if query:
        # Search for chamas by name
        chamas = Chama.query.filter(
            Chama.name.ilike(f'%{query}%'),
            Chama.status == 'active'
        ).all()
        
        # Filter out chamas user is already a member of
        user_chama_ids = [chama.id for chama in current_user.chamas]
        chamas = [chama for chama in chamas if chama.id not in user_chama_ids]
    
    return render_template('chama/search.html', chamas=chamas, query=query)

@chama_bp.route('/<int:chama_id>/request-join', methods=['POST'])
@login_required
def request_join_chama(chama_id):
    """Request to join a chama"""
    try:
        chama = Chama.query.get_or_404(chama_id)
        
        # Check if user is already a member
        if current_user in chama.members:
            return jsonify({'success': False, 'message': 'You are already a member of this chama'}), 400
        
        # Check if there's already a pending request
        existing_request = ChamaMembershipRequest.query.filter(
            ChamaMembershipRequest.user_id == current_user.id,
            ChamaMembershipRequest.chama_id == chama_id,
            ChamaMembershipRequest.status == 'pending'
        ).first()
        
        if existing_request:
            return jsonify({'success': False, 'message': 'You already have a pending request for this chama'}), 400
        
        # Create join request
        request_obj = ChamaMembershipRequest(
            user_id=current_user.id,
            chama_id=chama_id,
            request_type='join',
            status='pending'
        )
        
        db.session.add(request_obj)
        db.session.commit()
        
        # Send notification to admins
        admins = chama.admins
        for admin in admins:
            notification = Notification(
                user_id=admin.id,
                chama_id=chama_id,
                type='membership_request',
                title='New Join Request',
                message=f'{current_user.username} wants to join {chama.name}',
                data={
                    'request_id': request_obj.id,
                    'requester_name': current_user.username,
                    'chama_name': chama.name
                }
            )
            db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Join request sent successfully! Admins will review your request.'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@chama_bp.route('/<int:chama_id>/members/<int:member_id>/remove', methods=['POST'])
@login_required
def remove_chama_member(chama_id, member_id):
    """Remove a member from chama (admin only)"""
    try:
        chama = Chama.query.get_or_404(chama_id)
        
        # Check if current user is admin
        if not chama.is_admin(current_user.id):
            return jsonify({'success': False, 'message': 'Only admins can remove members'}), 403
        
        # Check if admin can remove this member
        if not chama.can_remove_member(current_user.id, member_id):
            return jsonify({'success': False, 'message': 'Cannot remove this member'}), 403
        
        # Get member to remove
        member = User.query.get_or_404(member_id)
        
        # Remove member
        success, message = chama.remove_member(member_id)
        
        if success:
            # Send notification to removed member
            notification = Notification(
                user_id=member_id,
                chama_id=chama_id,
                type='membership_removed',
                title='Removed from Chama',
                message=f'You have been removed from {chama.name}',
                data={
                    'chama_name': chama.name,
                    'removed_by': current_user.username
                }
            )
            db.session.add(notification)
            db.session.commit()
            
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@chama_bp.route('/<int:chama_id>/members/<int:member_id>/make-admin', methods=['POST'])
@login_required
def make_chama_admin(chama_id, member_id):
    """Make a member an admin (creator only)"""
    try:
        chama = Chama.query.get_or_404(chama_id)
        
        # Only creator can make new admins
        if current_user.id != chama.creator_id:
            return jsonify({'success': False, 'message': 'Only the chama creator can make new admins'}), 403
        
        # Update member role to admin
        stmt = chama_members.update().where(
            chama_members.c.user_id == member_id,
            chama_members.c.chama_id == chama_id
        ).values(role='admin')
        
        result = db.session.execute(stmt)
        
        if result.rowcount > 0:
            # Send notification to new admin
            member = User.query.get(member_id)
            notification = Notification(
                user_id=member_id,
                chama_id=chama_id,
                type='admin_promotion',
                title='Promoted to Admin',
                message=f'You have been promoted to admin in {chama.name}',
                data={
                    'chama_name': chama.name,
                    'promoted_by': current_user.username
                }
            )
            db.session.add(notification)
            db.session.commit()
            
            return jsonify({'success': True, 'message': f'{member.username} is now an admin'})
        else:
            return jsonify({'success': False, 'message': 'Member not found'}), 404
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@chama_bp.route('/<int:chama_id>/verify-payment', methods=['GET', 'POST'])
@login_required
@chama_member_required
def verify_payment(chama_id):
    """Manual payment verification using M-Pesa message"""
    chama = Chama.query.get_or_404(chama_id)
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            mpesa_message = data.get('mpesa_message', '').strip()
            payment_type = data.get('payment_type')
            amount = float(data.get('amount', 0))
            
            if not mpesa_message or not payment_type or amount <= 0:
                return jsonify({'success': False, 'message': 'All fields are required'}), 400
            
            # Extract transaction ID from M-Pesa message (simple regex)
            import re
            transaction_id_match = re.search(r'[A-Z0-9]{10}', mpesa_message)
            transaction_id = transaction_id_match.group() if transaction_id_match else None
            
            # Create verification record
            verification = ManualPaymentVerification(
                user_id=current_user.id,
                chama_id=chama_id,
                payment_type=payment_type,
                amount=amount,
                mpesa_message=mpesa_message,
                transaction_id=transaction_id,
                verification_status='pending'
            )
            
            db.session.add(verification)
            
            # Send notification to admins
            admins = chama.admins
            for admin in admins:
                notification = Notification(
                    user_id=admin.id,
                    chama_id=chama_id,
                    type='payment_verification',
                    title='Payment Verification Required',
                    message=f'{current_user.username} submitted payment verification for {payment_type}',
                    data={
                        'verification_id': verification.id,
                        'amount': amount,
                        'payment_type': payment_type,
                        'user_name': current_user.username
                    }
                )
                db.session.add(notification)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Payment verification submitted. Admins will verify shortly.'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
    
    return render_template('chama/verify_payment.html', chama=chama)

@chama_bp.route('/<int:chama_id>/payment-verifications')
@login_required
@chama_admin_required
def payment_verifications(chama_id):
    """View pending payment verifications (admin only)"""
    chama = Chama.query.get_or_404(chama_id)
    
    verifications = ManualPaymentVerification.query.filter(
        ManualPaymentVerification.chama_id == chama_id
    ).order_by(ManualPaymentVerification.created_at.desc()).all()
    
    user_role = get_user_chama_role(current_user.id, chama_id)
    
    return render_template('chama/payment_verifications.html',
                         chama=chama,
                         verifications=verifications,
                         user_role=user_role)

@chama_bp.route('/verify-payment/<int:verification_id>/approve', methods=['POST'])
@login_required
def approve_payment_verification(verification_id):
    """Approve a payment verification (admin only)"""
    try:
        verification = ManualPaymentVerification.query.get_or_404(verification_id)
        chama = verification.chama
        
        # Check if current user is admin
        if not chama.is_admin(current_user.id):
            return jsonify({'success': False, 'message': 'Only admins can approve payments'}), 403
        
        data = request.get_json()
        notes = data.get('notes', '')
        
        # Update verification
        verification.verification_status = 'verified'
        verification.verified_by = current_user.id
        verification.verified_at = datetime.utcnow()
        verification.verification_notes = notes
        
        # Process the payment based on type
        if verification.payment_type == 'contribution':
            # Create transaction record
            transaction = Transaction(
                type='contribution',
                amount=verification.amount,
                description=f"Manual verification - {verification.transaction_id}",
                user_id=verification.user_id,
                chama_id=chama.id
            )
            db.session.add(transaction)
            
            # Update chama balance
            chama.total_balance += verification.amount
            
        elif verification.payment_type == 'registration_fee':
            # Create registration fee payment record
            payment = RegistrationFeePayment(
                user_id=verification.user_id,
                chama_id=chama.id,
                amount=verification.amount,
                mpesa_receipt_number=verification.transaction_id,
                payment_status='completed',
                payment_date=datetime.utcnow()
            )
            db.session.add(payment)
        
        # Send notification to user
        notification = Notification(
            user_id=verification.user_id,
            chama_id=chama.id,
            type='payment_approved',
            title='Payment Verified',
            message=f'Your {verification.payment_type} payment has been verified and approved',
            data={
                'amount': verification.amount,
                'payment_type': verification.payment_type,
                'verified_by': current_user.username
            }
        )
        db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Payment verification approved successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@chama_bp.route('/verify-payment/<int:verification_id>/reject', methods=['POST'])
@login_required
def reject_payment_verification(verification_id):
    """Reject a payment verification (admin only)"""
    try:
        verification = ManualPaymentVerification.query.get_or_404(verification_id)
        chama = verification.chama
        
        # Check if current user is admin
        if not chama.is_admin(current_user.id):
            return jsonify({'success': False, 'message': 'Only admins can reject payments'}), 403
        
        data = request.get_json()
        notes = data.get('notes', '')
        
        if not notes.strip():
            return jsonify({'success': False, 'message': 'Please provide a reason for rejection'}), 400
        
        # Update verification
        verification.verification_status = 'rejected'
        verification.verified_by = current_user.id
        verification.verified_at = datetime.utcnow()
        verification.verification_notes = notes
        
        # Send notification to user
        notification = Notification(
            user_id=verification.user_id,
            chama_id=chama.id,
            type='payment_rejected',
            title='Payment Verification Rejected',
            message=f'Your {verification.payment_type} payment verification has been rejected',
            data={
                'verification_id': verification.id,
                'amount': verification.amount,
                'payment_type': verification.payment_type,
                'rejection_reason': notes
            }
        )
        db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Payment verification rejected successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

def get_user_chama_role(user_id, chama_id):
    """Get the role of a user in a specific chama"""
    membership = db.session.query(chama_members).filter(
        chama_members.c.user_id == user_id,
        chama_members.c.chama_id == chama_id
    ).first()
    
    return membership.role if membership else None
