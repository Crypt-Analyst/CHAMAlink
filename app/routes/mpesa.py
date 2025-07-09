from flask import Blueprint, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import Chama, Transaction, MpesaTransaction, User
from app.utils.mpesa import mpesa_api
from app.utils.permissions import user_can_access_chama
from app import db
from datetime import datetime

mpesa_bp = Blueprint('mpesa', __name__, url_prefix='/mpesa')

@mpesa_bp.route('/initiate_payment', methods=['POST'])
@login_required
def initiate_payment():
    """Initiate M-Pesa STK push for contribution"""
    try:
        data = request.get_json()
        chama_id = data.get('chama_id')
        amount = float(data.get('amount', 0))
        phone_number = data.get('phone_number') or current_user.phone_number
        
        # Validate inputs
        if not chama_id or amount <= 0:
            return jsonify({'success': False, 'message': 'Invalid chama or amount'}), 400
        
        if not phone_number:
            return jsonify({'success': False, 'message': 'Phone number is required'}), 400
        
        # Check if user can access this chama
        if not user_can_access_chama(current_user.id, chama_id):
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        chama = Chama.query.get(chama_id)
        if not chama:
            return jsonify({'success': False, 'message': 'Chama not found'}), 404
        
        # Create transaction record first
        transaction = Transaction(
            type='contribution',
            amount=amount,
            description=f'Contribution to {chama.name}',
            status='pending',
            user_id=current_user.id,
            chama_id=chama_id
        )
        db.session.add(transaction)
        db.session.flush()  # Get transaction ID
        
        # Initiate M-Pesa payment
        account_reference = f"CHAMA{chama_id}T{transaction.id}"
        transaction_desc = f"Contribution to {chama.name}"
        
        mpesa_result = mpesa_api.stk_push(
            phone_number=phone_number,
            amount=amount,
            account_reference=account_reference,
            transaction_desc=transaction_desc
        )
        
        if mpesa_result.get('success'):
            # Create M-Pesa transaction record
            mpesa_transaction = MpesaTransaction(
                checkout_request_id=mpesa_result['checkout_request_id'],
                merchant_request_id=mpesa_result['merchant_request_id'],
                amount=amount,
                phone_number=phone_number,
                account_reference=account_reference,
                transaction_desc=transaction_desc,
                status='pending',
                user_id=current_user.id,
                chama_id=chama_id,
                transaction_id=transaction.id
            )
            db.session.add(mpesa_transaction)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Payment initiated successfully. Please check your phone for the M-Pesa prompt.',
                'checkout_request_id': mpesa_result['checkout_request_id']
            })
        else:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': mpesa_result.get('message', 'Payment initiation failed')
            }), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@mpesa_bp.route('/check_payment_status', methods=['POST'])
@login_required
def check_payment_status():
    """Check the status of an M-Pesa payment"""
    try:
        data = request.get_json()
        checkout_request_id = data.get('checkout_request_id')
        
        if not checkout_request_id:
            return jsonify({'success': False, 'message': 'Checkout request ID is required'}), 400
        
        # Get the M-Pesa transaction
        mpesa_transaction = MpesaTransaction.query.filter_by(
            checkout_request_id=checkout_request_id,
            user_id=current_user.id
        ).first()
        
        if not mpesa_transaction:
            return jsonify({'success': False, 'message': 'Transaction not found'}), 404
        
        # Check payment status with M-Pesa
        status_result = mpesa_api.query_transaction_status(checkout_request_id)
        
        if status_result.get('ResultCode') == '0':
            # Payment successful
            mpesa_transaction.status = 'completed'
            mpesa_transaction.mpesa_receipt_number = status_result.get('MpesaReceiptNumber')
            mpesa_transaction.transaction_date = datetime.now()
            mpesa_transaction.result_code = status_result.get('ResultCode')
            mpesa_transaction.result_desc = status_result.get('ResultDesc')
            
            # Update the main transaction
            transaction = mpesa_transaction.transaction
            transaction.status = 'completed'
            
            # Update chama balance
            chama = Chama.query.get(mpesa_transaction.chama_id)
            chama.total_balance += mpesa_transaction.amount
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'status': 'completed',
                'message': 'Payment completed successfully',
                'receipt_number': mpesa_transaction.mpesa_receipt_number
            })
        elif status_result.get('ResultCode') == '1032':
            # Payment cancelled by user
            mpesa_transaction.status = 'failed'
            mpesa_transaction.result_code = status_result.get('ResultCode')
            mpesa_transaction.result_desc = 'Payment cancelled by user'
            
            transaction = mpesa_transaction.transaction
            transaction.status = 'failed'
            
            db.session.commit()
            
            return jsonify({
                'success': False,
                'status': 'cancelled',
                'message': 'Payment was cancelled'
            })
        else:
            # Payment still pending or failed
            status = 'pending' if status_result.get('ResultCode') == '1037' else 'failed'
            return jsonify({
                'success': True,
                'status': status,
                'message': status_result.get('ResultDesc', 'Payment pending')
            })
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@mpesa_bp.route('/callback', methods=['POST'])
def mpesa_callback():
    """Handle M-Pesa callback"""
    try:
        callback_data = request.get_json()
        
        # Extract relevant data from callback
        result_code = callback_data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
        result_desc = callback_data.get('Body', {}).get('stkCallback', {}).get('ResultDesc')
        checkout_request_id = callback_data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
        
        # Find the M-Pesa transaction
        mpesa_transaction = MpesaTransaction.query.filter_by(
            checkout_request_id=checkout_request_id
        ).first()
        
        if not mpesa_transaction:
            return jsonify({'success': False, 'message': 'Transaction not found'}), 404
        
        # Update transaction status
        mpesa_transaction.result_code = str(result_code)
        mpesa_transaction.result_desc = result_desc
        
        if result_code == 0:
            # Payment successful
            callback_metadata = callback_data.get('Body', {}).get('stkCallback', {}).get('CallbackMetadata', {})
            items = callback_metadata.get('Item', [])
            
            for item in items:
                if item.get('Name') == 'MpesaReceiptNumber':
                    mpesa_transaction.mpesa_receipt_number = item.get('Value')
                elif item.get('Name') == 'TransactionDate':
                    mpesa_transaction.transaction_date = datetime.now()
            
            mpesa_transaction.status = 'completed'
            
            # Update main transaction
            transaction = mpesa_transaction.transaction
            transaction.status = 'completed'
            
            # Update chama balance
            chama = Chama.query.get(mpesa_transaction.chama_id)
            chama.total_balance += mpesa_transaction.amount
            
        else:
            # Payment failed
            mpesa_transaction.status = 'failed'
            transaction = mpesa_transaction.transaction
            transaction.status = 'failed'
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Callback processed'}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
