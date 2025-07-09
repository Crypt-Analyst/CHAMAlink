from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.chama import Chama, MultiSignatureTransaction, Loan
from app.models.user import User
from app.utils.sms_service import send_loan_disbursement_sms
from app.routes.decorators import chama_admin_required, chama_member_required
from app import db
from datetime import datetime
import uuid

multisig_bp = Blueprint('multisig', __name__)

@multisig_bp.route('/chama/<int:chama_id>/multi-signature')
@login_required
@chama_admin_required
def dashboard(chama_id):
    """Multi-signature transactions dashboard"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Get pending transactions requiring signatures
    pending_transactions = MultiSignatureTransaction.query.filter_by(
        chama_id=chama_id,
        status='pending'
    ).order_by(MultiSignatureTransaction.created_at.desc()).all()
    
    # Get partially signed transactions
    partially_signed = MultiSignatureTransaction.query.filter_by(
        chama_id=chama_id,
        status='partially_signed'
    ).order_by(MultiSignatureTransaction.created_at.desc()).all()
    
    # Get recent completed transactions
    completed_transactions = MultiSignatureTransaction.query.filter(
        MultiSignatureTransaction.chama_id == chama_id,
        MultiSignatureTransaction.status.in_(['approved', 'rejected', 'executed'])
    ).order_by(MultiSignatureTransaction.updated_at.desc()).limit(10).all()
    
    return render_template('multisig/dashboard.html',
                           chama=chama,
                           pending_transactions=pending_transactions,
                           partially_signed=partially_signed,
                           completed_transactions=completed_transactions)

@multisig_bp.route('/chama/<int:chama_id>/multi-signature/<int:transaction_id>')
@login_required
@chama_member_required
def transaction_detail(chama_id, transaction_id):
    """View multi-signature transaction details"""
    chama = Chama.query.get_or_404(chama_id)
    transaction = MultiSignatureTransaction.query.get_or_404(transaction_id)
    
    if transaction.chama_id != chama_id:
        flash('Transaction not found.', 'error')
        return redirect(url_for('multisig.dashboard', chama_id=chama_id))
    
    # Get related loan if applicable
    related_loan = None
    if transaction.transaction_type == 'loan_disbursement':
        related_loan = Loan.query.get(transaction.transaction_reference_id)
    
    return render_template('multisig/transaction_detail.html',
                           chama=chama,
                           transaction=transaction,
                           related_loan=related_loan)

@multisig_bp.route('/chama/<int:chama_id>/multi-signature/<int:transaction_id>/sign', methods=['POST'])
@login_required
@chama_admin_required
def sign_transaction(chama_id, transaction_id):
    """Sign a multi-signature transaction"""
    chama = Chama.query.get_or_404(chama_id)
    transaction = MultiSignatureTransaction.query.get_or_404(transaction_id)
    
    if transaction.chama_id != chama_id:
        return jsonify({'success': False, 'message': 'Transaction not found'})
    
    comment = request.form.get('comment', '')
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
    
    try:
        success, message = transaction.add_signature(
            signatory_id=current_user.id,
            comment=comment,
            ip_address=ip_address
        )
        
        if success:
            db.session.commit()
            
            # If fully approved, handle disbursement for loans
            if transaction.status == 'approved' and transaction.transaction_type == 'loan_disbursement':
                loan = Loan.query.get(transaction.transaction_reference_id)
                if loan:
                    # Update loan status
                    loan.status = 'disbursed'
                    transaction.status = 'executed'
                    transaction.executed_at = datetime.utcnow()
                    
                    # Send SMS notification
                    send_loan_disbursement_sms(
                        user=loan.user,
                        chama=chama,
                        amount=loan.amount,
                        mpesa_number=loan.disbursement_details.get('phone', 'N/A') if loan.disbursement_details else 'N/A'
                    )
                    
                    db.session.commit()
            
            return jsonify({
                'success': True,
                'message': message,
                'status': transaction.status,
                'signatures_required': transaction.signatures_required
            })
        else:
            return jsonify({'success': False, 'message': message})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error signing transaction: {str(e)}'})

@multisig_bp.route('/chama/<int:chama_id>/multi-signature/<int:transaction_id>/reject', methods=['POST'])
@login_required
@chama_admin_required
def reject_transaction(chama_id, transaction_id):
    """Reject a multi-signature transaction"""
    chama = Chama.query.get_or_404(chama_id)
    transaction = MultiSignatureTransaction.query.get_or_404(transaction_id)
    
    if transaction.chama_id != chama_id:
        return jsonify({'success': False, 'message': 'Transaction not found'})
    
    reason = request.form.get('reason', 'No reason provided')
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
    
    try:
        success, message = transaction.reject_transaction(
            rejector_id=current_user.id,
            reason=reason,
            ip_address=ip_address
        )
        
        if success:
            # If this was a loan disbursement, update loan status
            if transaction.transaction_type == 'loan_disbursement':
                loan = Loan.query.get(transaction.transaction_reference_id)
                if loan:
                    loan.status = 'approved'  # Return to approved state
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': message,
                'status': transaction.status
            })
        else:
            return jsonify({'success': False, 'message': message})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error rejecting transaction: {str(e)}'})

@multisig_bp.route('/chama/<int:chama_id>/loans/<int:loan_id>/request-disbursement', methods=['POST'])
@login_required
@chama_admin_required
def request_loan_disbursement(chama_id, loan_id):
    """Request multi-signature approval for loan disbursement"""
    chama = Chama.query.get_or_404(chama_id)
    loan = Loan.query.get_or_404(loan_id)
    
    if loan.chama_id != chama_id:
        return jsonify({'success': False, 'message': 'Loan not found'})
    
    if loan.status != 'approved':
        return jsonify({'success': False, 'message': 'Loan must be approved first'})
    
    if loan.multi_sig_transaction_id:
        return jsonify({'success': False, 'message': 'Disbursement request already exists'})
    
    try:
        # Get disbursement details from form
        disbursement_method = request.form.get('disbursement_method', 'mpesa')
        phone_number = request.form.get('phone_number', '')
        bank_account = request.form.get('bank_account', '')
        
        # Store disbursement details
        if disbursement_method == 'mpesa':
            loan.disbursement_details = {'method': 'mpesa', 'phone': phone_number}
        elif disbursement_method == 'bank_transfer':
            loan.disbursement_details = {'method': 'bank_transfer', 'account': bank_account}
        else:
            loan.disbursement_details = {'method': 'cash'}
        
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        
        transaction = loan.create_disbursement_transaction(
            requested_by_id=current_user.id,
            ip_address=ip_address
        )
        
        if transaction:
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Disbursement request created successfully. Awaiting signatures.',
                'transaction_id': transaction.id
            })
        else:
            return jsonify({'success': False, 'message': 'Could not create disbursement request'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error creating disbursement request: {str(e)}'})

@multisig_bp.route('/chama/<int:chama_id>/multi-signature/create-expense', methods=['GET', 'POST'])
@login_required
@chama_admin_required
def create_expense_transaction(chama_id):
    """Create multi-signature transaction for large expenses"""
    chama = Chama.query.get_or_404(chama_id)
    
    if request.method == 'GET':
        return render_template('multisig/create_expense.html', chama=chama)
    
    try:
        amount = float(request.form.get('amount', 0))
        description = request.form.get('description', '')
        expense_category = request.form.get('category', 'general')
        
        if amount <= 0:
            flash('Amount must be greater than zero.', 'error')
            return redirect(url_for('multisig.create_expense_transaction', chama_id=chama_id))
        
        if not description:
            flash('Description is required.', 'error')
            return redirect(url_for('multisig.create_expense_transaction', chama_id=chama_id))
        
        # Large expenses above KES 5,000 require multi-signature
        if amount < 5000:
            flash('Multi-signature is only required for expenses above KES 5,000.', 'warning')
            return redirect(url_for('multisig.create_expense_transaction', chama_id=chama_id))
        
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        
        transaction = MultiSignatureTransaction.create_large_expense_transaction(
            chama_id=chama_id,
            amount=amount,
            description=f'{expense_category.title()}: {description}',
            requested_by_id=current_user.id,
            ip_address=ip_address
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        flash('Expense approval request created successfully. Awaiting signatures.', 'success')
        return redirect(url_for('multisig.transaction_detail', chama_id=chama_id, transaction_id=transaction.id))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating expense request: {str(e)}', 'error')
        return redirect(url_for('multisig.create_expense_transaction', chama_id=chama_id))

@multisig_bp.route('/api/chama/<int:chama_id>/multi-signature/stats')
@login_required
@chama_member_required
def multisig_stats(chama_id):
    """API endpoint for multi-signature statistics"""
    chama = Chama.query.get_or_404(chama_id)
    
    pending_count = MultiSignatureTransaction.query.filter_by(
        chama_id=chama_id,
        status='pending'
    ).count()
    
    partially_signed_count = MultiSignatureTransaction.query.filter_by(
        chama_id=chama_id,
        status='partially_signed'
    ).count()
    
    # Check if current user has pending signatures
    user_pending_signatures = MultiSignatureTransaction.query.filter(
        MultiSignatureTransaction.chama_id == chama_id,
        MultiSignatureTransaction.status.in_(['pending', 'partially_signed']),
        MultiSignatureTransaction.first_signatory_id != current_user.id,
        MultiSignatureTransaction.second_signatory_id != current_user.id
    ).count()
    
    return jsonify({
        'pending_transactions': pending_count,
        'partially_signed': partially_signed_count,
        'user_pending_signatures': user_pending_signatures,
        'total_requiring_attention': pending_count + partially_signed_count
    })
