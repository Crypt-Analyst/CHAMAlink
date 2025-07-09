from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import (
    Chama, LoanApplication, LoanApproval, Transaction, 
    Notification, MpesaTransaction, chama_members
)
from app.utils.permissions import chama_member_required, chama_admin_required, user_can_access_chama
from app.utils.mpesa import initiate_stk_push
from app import db
from datetime import datetime, timedelta
from sqlalchemy import desc, and_

loans_bp = Blueprint('loans', __name__, url_prefix='/loans')

@loans_bp.route('/')
@login_required
def loan_dashboard():
    """Dashboard for loan applications"""
    # Get user's loan applications
    user_loans = LoanApplication.query.filter_by(user_id=current_user.id).order_by(desc(LoanApplication.application_date)).all()
    
    # Get loans pending approval if user is an admin
    pending_approvals = []
    user_chamas = current_user.chamas
    
    for chama in user_chamas:
        # Check if user is admin in this chama
        user_role = db.session.query(chama_members.c.role).filter(
            and_(chama_members.c.user_id == current_user.id, 
                 chama_members.c.chama_id == chama.id)
        ).scalar()
        
        if user_role in ['admin', 'creator']:
            chama_pending = LoanApplication.query.filter_by(
                chama_id=chama.id, 
                status='pending'
            ).all()
            pending_approvals.extend(chama_pending)
    
    return render_template('loans/dashboard.html',
                         user_loans=user_loans,
                         pending_approvals=pending_approvals)

@loans_bp.route('/apply/<int:chama_id>')
@login_required
@chama_member_required
def apply_loan(chama_id):
    """Apply for a loan form"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Check if user has pending loan applications
    existing_pending = LoanApplication.query.filter_by(
        user_id=current_user.id,
        chama_id=chama_id,
        status='pending'
    ).first()
    
    if existing_pending:
        flash('You already have a pending loan application for this chama', 'warning')
        return redirect(url_for('loans.loan_dashboard'))
    
    # Check if user has unpaid loans
    unpaid_loans = LoanApplication.query.filter_by(
        user_id=current_user.id,
        chama_id=chama_id,
        status='disbursed'
    ).filter(LoanApplication.remaining_amount > 0).all()
    
    if unpaid_loans:
        flash('You have unpaid loans. Please clear them before applying for a new loan', 'warning')
        return redirect(url_for('loans.loan_dashboard'))
    
    return render_template('loans/apply.html', chama=chama)

@loans_bp.route('/submit_application', methods=['POST'])
@login_required
def submit_application():
    """Submit loan application"""
    try:
        data = request.get_json()
        chama_id = data.get('chama_id')
        amount = float(data.get('amount', 0))
        purpose = data.get('purpose', '').strip()
        repayment_period = int(data.get('repayment_period', 0))
        
        # Validation
        if not chama_id:
            return jsonify({'success': False, 'message': 'Chama ID is required'}), 400
        
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Amount must be greater than 0'}), 400
        
        if not purpose:
            return jsonify({'success': False, 'message': 'Purpose is required'}), 400
        
        if repayment_period <= 0:
            return jsonify({'success': False, 'message': 'Repayment period must be greater than 0'}), 400
        
        # Security check
        if not user_can_access_chama(current_user.id, chama_id):
            return jsonify({'success': False, 'message': 'You do not have access to this chama'}), 403
        
        # Check chama balance
        chama = Chama.query.get(chama_id)
        if chama.total_balance < amount:
            return jsonify({'success': False, 'message': 'Insufficient funds in chama'}), 400
        
        # Create loan application
        loan_application = LoanApplication(
            amount=amount,
            purpose=purpose,
            repayment_period=repayment_period,
            interest_rate=0.0,  # Can be configured per chama
            user_id=current_user.id,
            chama_id=chama_id,
            due_date=datetime.utcnow() + timedelta(days=repayment_period * 30)
        )
        
        db.session.add(loan_application)
        db.session.commit()
        
        # Notify admins
        create_loan_notification(loan_application)
        
        return jsonify({'success': True, 'message': 'Loan application submitted successfully!'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@loans_bp.route('/approve/<int:loan_id>', methods=['POST'])
@login_required
def approve_loan(loan_id):
    """Approve or reject loan application"""
    try:
        data = request.get_json()
        action = data.get('action')  # 'approve' or 'reject'
        comments = data.get('comments', '').strip()
        
        loan_application = LoanApplication.query.get_or_404(loan_id)
        
        # Security check - only admins can approve
        user_role = db.session.query(chama_members.c.role).filter(
            and_(chama_members.c.user_id == current_user.id, 
                 chama_members.c.chama_id == loan_application.chama_id)
        ).scalar()
        
        if user_role not in ['admin', 'creator']:
            return jsonify({'success': False, 'message': 'You do not have permission to approve loans'}), 403
        
        # Check if already approved by this admin
        existing_approval = LoanApproval.query.filter_by(
            loan_application_id=loan_id,
            admin_id=current_user.id
        ).first()
        
        if existing_approval:
            return jsonify({'success': False, 'message': 'You have already voted on this loan'}), 400
        
        # Create approval record
        approval = LoanApproval(
            loan_application_id=loan_id,
            admin_id=current_user.id,
            status=action,
            comments=comments
        )
        
        db.session.add(approval)
        
        # Check if loan should be approved (3 approvals required)
        if action == 'approve':
            approval_count = loan_application.approval_count + 1
            
            if approval_count >= 3:
                loan_application.status = 'approved'
                loan_application.approval_date = datetime.utcnow()
                
                # Notify user
                notification = Notification(
                    title='Loan Approved',
                    message=f'Your loan application for {loan_application.formatted_amount} has been approved',
                    type='loan',
                    user_id=loan_application.user_id,
                    chama_id=loan_application.chama_id
                )
                db.session.add(notification)
        
        # Check if loan should be rejected (any rejection)
        elif action == 'reject':
            loan_application.status = 'rejected'
            
            # Notify user
            notification = Notification(
                title='Loan Rejected',
                message=f'Your loan application for {loan_application.formatted_amount} has been rejected',
                type='loan',
                user_id=loan_application.user_id,
                chama_id=loan_application.chama_id
            )
            db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Loan {action}d successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@loans_bp.route('/disburse/<int:loan_id>', methods=['POST'])
@login_required
def disburse_loan(loan_id):
    """Disburse approved loan via M-Pesa"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number', '').strip()
        
        loan_application = LoanApplication.query.get_or_404(loan_id)
        
        # Security check - only admins can disburse
        user_role = db.session.query(chama_members.c.role).filter(
            and_(chama_members.c.user_id == current_user.id, 
                 chama_members.c.chama_id == loan_application.chama_id)
        ).scalar()
        
        if user_role not in ['admin', 'creator']:
            return jsonify({'success': False, 'message': 'You do not have permission to disburse loans'}), 403
        
        # Check if loan is approved
        if loan_application.status != 'approved':
            return jsonify({'success': False, 'message': 'Loan is not approved for disbursement'}), 400
        
        # Validate phone number
        if not phone_number:
            return jsonify({'success': False, 'message': 'Phone number is required'}), 400
        
        # Check chama balance
        chama = Chama.query.get(loan_application.chama_id)
        if chama.total_balance < loan_application.amount:
            return jsonify({'success': False, 'message': 'Insufficient funds in chama'}), 400
        
        # Initiate M-Pesa payment
        mpesa_response = initiate_stk_push(
            phone_number=phone_number,
            amount=loan_application.amount,
            account_reference=f"LOAN-{loan_application.id}",
            transaction_desc=f"Loan disbursement - {loan_application.purpose}"
        )
        
        if mpesa_response['success']:
            # Update loan status
            loan_application.status = 'disbursed'
            loan_application.disbursement_date = datetime.utcnow()
            
            # Create transaction record
            transaction = Transaction(
                type='loan',
                amount=loan_application.amount,
                description=f"Loan disbursement - {loan_application.purpose}",
                user_id=loan_application.user_id,
                chama_id=loan_application.chama_id
            )
            
            # Update chama balance
            chama.total_balance -= loan_application.amount
            
            # Create M-Pesa transaction record
            mpesa_transaction = MpesaTransaction(
                checkout_request_id=mpesa_response['checkout_request_id'],
                amount=loan_application.amount,
                phone_number=phone_number,
                account_reference=f"LOAN-{loan_application.id}",
                transaction_desc=f"Loan disbursement - {loan_application.purpose}",
                user_id=loan_application.user_id,
                chama_id=loan_application.chama_id
            )
            
            db.session.add(transaction)
            db.session.add(mpesa_transaction)
            
            # Notify user
            notification = Notification(
                title='Loan Disbursed',
                message=f'Your loan of {loan_application.formatted_amount} has been disbursed to your M-Pesa',
                type='loan',
                user_id=loan_application.user_id,
                chama_id=loan_application.chama_id
            )
            db.session.add(notification)
            
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Loan disbursed successfully! M-Pesa prompt sent.',
                'checkout_request_id': mpesa_response['checkout_request_id']
            })
        else:
            return jsonify({'success': False, 'message': mpesa_response['message']}), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@loans_bp.route('/repay/<int:loan_id>', methods=['POST'])
@login_required
def repay_loan(loan_id):
    """Repay loan via M-Pesa"""
    try:
        data = request.get_json()
        amount = float(data.get('amount', 0))
        phone_number = data.get('phone_number', '').strip()
        
        loan_application = LoanApplication.query.get_or_404(loan_id)
        
        # Security check - only loan owner can repay
        if loan_application.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'You can only repay your own loans'}), 403
        
        # Validation
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Amount must be greater than 0'}), 400
        
        if amount > loan_application.remaining_amount:
            return jsonify({'success': False, 'message': 'Amount exceeds remaining loan balance'}), 400
        
        if not phone_number:
            return jsonify({'success': False, 'message': 'Phone number is required'}), 400
        
        # Initiate M-Pesa payment
        mpesa_response = initiate_stk_push(
            phone_number=phone_number,
            amount=amount,
            account_reference=f"REPAY-{loan_application.id}",
            transaction_desc=f"Loan repayment - {loan_application.purpose}"
        )
        
        if mpesa_response['success']:
            # Update loan repayment amount
            loan_application.amount_paid += amount
            
            # Create transaction record
            transaction = Transaction(
                type='loan_repayment',
                amount=amount,
                description=f"Loan repayment - {loan_application.purpose}",
                user_id=current_user.id,
                chama_id=loan_application.chama_id
            )
            
            # Update chama balance
            chama = Chama.query.get(loan_application.chama_id)
            chama.total_balance += amount
            
            # Create M-Pesa transaction record
            mpesa_transaction = MpesaTransaction(
                checkout_request_id=mpesa_response['checkout_request_id'],
                amount=amount,
                phone_number=phone_number,
                account_reference=f"REPAY-{loan_application.id}",
                transaction_desc=f"Loan repayment - {loan_application.purpose}",
                user_id=current_user.id,
                chama_id=loan_application.chama_id,
                transaction_id=transaction.id
            )
            
            db.session.add(transaction)
            db.session.add(mpesa_transaction)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Loan repayment initiated successfully! M-Pesa prompt sent.',
                'checkout_request_id': mpesa_response['checkout_request_id']
            })
        else:
            return jsonify({'success': False, 'message': mpesa_response['message']}), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

def create_loan_notification(loan_application):
    """Create notifications for admins about new loan application"""
    chama = Chama.query.get(loan_application.chama_id)
    
    # Get all admins for this chama
    admins = db.session.query(chama_members.c.user_id).filter(
        and_(chama_members.c.chama_id == loan_application.chama_id,
             chama_members.c.role.in_(['admin', 'creator']))
    ).all()
    
    for admin_id_tuple in admins:
        admin_id = admin_id_tuple[0]
        notification = Notification(
            title='New Loan Application',
            message=f'{loan_application.user.username} has applied for a loan of {loan_application.formatted_amount} in {chama.name}',
            type='loan',
            user_id=admin_id,
            chama_id=loan_application.chama_id
        )
        db.session.add(notification)

def get_user_chama_role(user_id, chama_id):
    """Get user's role in a specific chama"""
    return db.session.query(chama_members.c.role).filter(
        and_(chama_members.c.user_id == user_id, 
             chama_members.c.chama_id == chama_id)
    ).scalar()
