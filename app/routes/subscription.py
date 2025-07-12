from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app import db
from app.models.subscription import SubscriptionPlan, UserSubscription, SubscriptionPayment
from app.utils.mpesa import initiate_subscription_payment
from app.utils.email_service import send_subscription_email
from datetime import datetime, timedelta
import logging

subscription_bp = Blueprint('subscription', __name__)

@subscription_bp.route('/plans')
@login_required
def plans():
    """Show available subscription plans with multi-month options"""
    from app.models.subscription import SubscriptionPlan, SubscriptionPlanPricing
    
    plans = SubscriptionPlan.query.filter_by(is_active=True).all()
    current_subscription = current_user.current_subscription
    
    # Get pricing options for each plan
    plans_with_pricing = []
    for plan in plans:
        pricing_options = SubscriptionPlanPricing.query.filter_by(
            plan_id=plan.id, 
            is_active=True
        ).order_by(SubscriptionPlanPricing.months).all()
        
        plans_with_pricing.append({
            'plan': plan,
            'pricing_options': pricing_options
        })
    
    return render_template('subscription/plans_new.html', 
                         plans_with_pricing=plans_with_pricing,
                         current_subscription=current_subscription)


@subscription_bp.route('/checkout')
@login_required
def checkout():
    """Checkout page for subscription payment"""
    plan_name = request.args.get('plan')
    duration = int(request.args.get('duration', 1))
    
    from app.models.subscription import SubscriptionPlan, SubscriptionPlanPricing
    
    # Get the plan
    plan = SubscriptionPlan.query.filter_by(name=plan_name).first()
    if not plan:
        flash('Invalid plan selected.', 'error')
        return redirect(url_for('subscription.plans'))
    
    # Get the pricing for the selected duration
    pricing = SubscriptionPlanPricing.query.filter_by(
        plan_id=plan.id,
        months=duration
    ).first()
    
    if not pricing:
        flash('Invalid duration selected.', 'error')
        return redirect(url_for('subscription.plans'))
    
    return render_template('subscription/checkout.html',
                         plan=plan,
                         pricing=pricing,
                         duration=duration)


@subscription_bp.route('/process-multi-month-payment', methods=['POST'])
@login_required
def process_multi_month_payment():
    """Process subscription payment"""
    data = request.get_json()
    
    plan_id = data.get('plan_id')
    pricing_id = data.get('pricing_id')
    phone_number = data.get('phone_number')
    
    from app.models.subscription import SubscriptionPlan, SubscriptionPlanPricing
    
    plan = SubscriptionPlan.query.get(plan_id)
    pricing = SubscriptionPlanPricing.query.get(pricing_id)
    
    if not plan or not pricing:
        return jsonify({'success': False, 'message': 'Invalid plan or pricing'})
    
    try:
        # Create payment record
        payment = SubscriptionPayment(
            user_id=current_user.id,
            pricing_id=pricing.id,
            amount=pricing.total_price,
            months_purchased=pricing.months,
            bonus_months=pricing.bonus_months,
            payment_status='pending'
        )
        
        db.session.add(payment)
        db.session.flush()  # Get payment ID
        
        # For now, simulate successful payment
        # In production, integrate with M-Pesa STK Push
        payment.payment_status = 'completed'
        payment.payment_date = datetime.utcnow()
        payment.mpesa_receipt_number = f"MOCK{payment.id:06d}"
        
        # Create or update user subscription
        current_subscription = current_user.current_subscription
        if current_subscription:
            # Extend existing subscription
            if current_subscription.end_date > datetime.utcnow():
                # Add to existing time
                start_date = current_subscription.end_date
            else:
                # Start fresh
                start_date = datetime.utcnow()
            
            current_subscription.end_date = start_date + timedelta(days=30 * payment.total_months_provided)
            current_subscription.status = 'active'
            current_subscription.is_trial = False
            payment.subscription_id = current_subscription.id
        else:
            # Create new subscription
            new_subscription = UserSubscription(
                user_id=current_user.id,
                plan_id=plan.id,
                status='active',
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=30 * payment.total_months_provided),
                is_trial=False
            )
            db.session.add(new_subscription)
            db.session.flush()
            payment.subscription_id = new_subscription.id
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Payment successful! Your {plan.name} subscription has been activated for {payment.total_months_provided} months.',
            'redirect_url': url_for('main.dashboard')
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Payment failed: {str(e)}'})

@subscription_bp.route('/subscribe/<int:plan_id>')
@login_required
def subscribe(plan_id):
    """Subscribe to a plan - redirect to payment options"""
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    duration = request.args.get('duration', 1, type=int)
    
    # Redirect to payment options page
    return redirect(url_for('subscription.payment_options', 
                          plan=plan.name, 
                          duration=duration))

@subscription_bp.route('/payment-options')
@login_required
def payment_options():
    """Show payment options page with skip trial functionality"""
    plan_name = request.args.get('plan')
    duration = int(request.args.get('duration', 1))
    
    from app.models.subscription import SubscriptionPlan, SubscriptionPlanPricing
    
    # Get the plan
    plan = SubscriptionPlan.query.filter_by(name=plan_name).first()
    if not plan:
        flash('Invalid plan selected.', 'error')
        return redirect(url_for('subscription.plans'))
    
    # Get the pricing for the selected duration
    pricing = SubscriptionPlanPricing.query.filter_by(
        plan_id=plan.id,
        months=duration
    ).first()
    
    if not pricing:
        flash('Invalid duration selected.', 'error')
        return redirect(url_for('subscription.plans'))
    
    return render_template('subscription/payment_options.html',
                         plan=plan,
                         pricing=pricing,
                         duration=duration)

@subscription_bp.route('/process-direct-payment', methods=['POST'])
@login_required
def process_direct_payment():
    """Process direct payment (skip trial)"""
    data = request.get_json()
    
    plan_id = data.get('plan_id')
    pricing_id = data.get('pricing_id')
    phone_number = data.get('phone_number')
    payment_method = data.get('payment_method', 'mpesa')
    skip_trial = data.get('skip_trial', False)
    
    from app.models.subscription import SubscriptionPlan, SubscriptionPlanPricing
    
    plan = SubscriptionPlan.query.get(plan_id)
    pricing = SubscriptionPlanPricing.query.get(pricing_id)
    
    if not plan or not pricing:
        return jsonify({'success': False, 'message': 'Invalid plan or pricing'})
    
    try:
        # Create payment record
        payment = SubscriptionPayment(
            user_id=current_user.id,
            pricing_id=pricing.id,
            amount=pricing.total_price,
            months_purchased=pricing.months,
            bonus_months=pricing.bonus_months,
            payment_status='pending',
            payment_method=payment_method
        )
        
        db.session.add(payment)
        db.session.flush()  # Get payment ID
        
        if payment_method == 'mpesa':
            # Initiate M-Pesa STK push
            from app.utils.mpesa import initiate_subscription_payment
            
            description = f"ChamaLink {plan.name.title()} Plan - {pricing.months}M"
            response = initiate_subscription_payment(
                phone_number=phone_number,
                amount=int(pricing.total_price),
                account_reference=f"DIRECT-{payment.id}",
                transaction_desc=description
            )
            
            if response and response.get('success'):
                # Store checkout request ID for callback processing
                payment.mpesa_receipt_number = response.get('checkout_request_id')
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'M-Pesa prompt sent! Please complete payment on your phone.',
                    'payment_id': payment.id,
                    'checkout_request_id': response.get('checkout_request_id')
                })
            else:
                payment.payment_status = 'failed'
                db.session.commit()
                return jsonify({
                    'success': False,
                    'message': response.get('message', 'M-Pesa payment initiation failed')
                })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Direct payment error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Payment processing failed. Please try again.'
        })

@subscription_bp.route('/process-bank-transfer', methods=['POST'])
@login_required
def process_bank_transfer():
    """Process bank transfer payment"""
    try:
        plan_id = request.form.get('plan_id')
        pricing_id = request.form.get('pricing_id')
        amount = float(request.form.get('amount'))
        transfer_reference = request.form.get('transfer_reference')
        transfer_date = request.form.get('transfer_date')
        sender_name = request.form.get('sender_name')
        transfer_notes = request.form.get('transfer_notes', '')
        
        from app.models.subscription import SubscriptionPlan, SubscriptionPlanPricing
        
        plan = SubscriptionPlan.query.get(plan_id)
        pricing = SubscriptionPlanPricing.query.get(pricing_id)
        
        if not plan or not pricing:
            return jsonify({'success': False, 'message': 'Invalid plan or pricing'})
        
        # Create bank transfer record
        from app.models.enterprise import BankTransferPayment  # We'll create this model
        
        bank_transfer = BankTransferPayment(
            user_id=current_user.id,
            plan_id=plan.id,
            pricing_id=pricing.id,
            amount=amount,
            transfer_reference=transfer_reference,
            transfer_date=datetime.strptime(transfer_date, '%Y-%m-%d').date(),
            sender_name=sender_name,
            notes=transfer_notes,
            bank_name='Cooperative Bank',
            account_number='01116844755200',
            paybill='400200',
            status='pending_verification'
        )
        
        db.session.add(bank_transfer)
        
        # Create corresponding subscription payment record
        payment = SubscriptionPayment(
            user_id=current_user.id,
            pricing_id=pricing.id,
            amount=amount,
            months_purchased=pricing.months,
            bonus_months=pricing.bonus_months,
            payment_status='pending_verification',
            payment_method='bank_transfer',
            bank_transfer_id=bank_transfer.id
        )
        
        db.session.add(payment)
        db.session.commit()
        
        # Send notification to admins for verification
        from app.models import Notification, User
        
        # Create admin notifications
        admin_users = User.query.filter_by(is_super_admin=True).all()
        for admin in admin_users:
            notification = Notification(
                user_id=admin.id,
                type='bank_transfer_verification',
                title='New Bank Transfer for Verification',
                message=f'{current_user.username} submitted bank transfer for {plan.name} plan',
                data={
                    'transfer_id': bank_transfer.id,
                    'payment_id': payment.id,
                    'amount': amount,
                    'sender': sender_name,
                    'reference': transfer_reference
                }
            )
            db.session.add(notification)
        
        db.session.commit()
        
        # Send confirmation email to user
        from app.utils.email_service import email_service
        email_service.send_bank_transfer_confirmation(
            current_user,
            bank_transfer,
            plan
        )
        
        return jsonify({
            'success': True,
            'message': 'Bank transfer confirmation submitted successfully! We will verify and activate your account within 24-48 hours.',
            'transfer_id': bank_transfer.id
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Bank transfer processing error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to process bank transfer confirmation. Please try again.'
        })

@subscription_bp.route('/payment-status/<int:payment_id>')
@login_required
def payment_status(payment_id):
    """Check payment status"""
    payment = SubscriptionPayment.query.get_or_404(payment_id)
    
    # Verify ownership
    if payment.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    return jsonify({
        'success': True,
        'status': payment.payment_status,
        'payment_id': payment.id,
        'amount': payment.amount
    })

@subscription_bp.route('/admin/bank-transfers')
@login_required
def admin_bank_transfers():
    """Admin page to view and manage bank transfers"""
    if not current_user.is_super_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    from app.models.enterprise import BankTransferPayment
    
    # Get all bank transfers, ordered by most recent first
    transfers = BankTransferPayment.query.order_by(
        BankTransferPayment.created_at.desc()
    ).all()
    
    # Count pending transfers
    pending_count = BankTransferPayment.query.filter_by(
        status='pending_verification'
    ).count()
    
    return render_template('admin/bank_transfers.html',
                         transfers=transfers,
                         pending_count=pending_count)

@subscription_bp.route('/verify-bank-transfer/<int:transfer_id>', methods=['POST'])
@login_required
def verify_bank_transfer(transfer_id):
    """Admin route to verify bank transfer"""
    if not current_user.is_super_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    from app.models.enterprise import BankTransferPayment
    
    transfer = BankTransferPayment.query.get_or_404(transfer_id)
    verification_status = request.json.get('status')  # 'approved' or 'rejected'
    admin_notes = request.json.get('notes', '')
    
    if verification_status == 'approved':
        # Update transfer status
        transfer.status = 'verified'
        transfer.verified_by = current_user.id
        transfer.verified_at = datetime.utcnow()
        transfer.admin_notes = admin_notes
        
        # Update payment status
        payment = SubscriptionPayment.query.filter_by(bank_transfer_id=transfer.id).first()
        if payment:
            payment.payment_status = 'completed'
            payment.payment_date = datetime.utcnow()
            
            # Create or update subscription
            user = transfer.user
            pricing = transfer.pricing
            
            current_subscription = user.current_subscription
            if current_subscription:
                # Extend existing subscription
                if current_subscription.end_date > datetime.utcnow():
                    start_date = current_subscription.end_date
                else:
                    start_date = datetime.utcnow()
                
                current_subscription.end_date = start_date + timedelta(days=30 * payment.total_months_provided)
                current_subscription.status = 'active'
                current_subscription.is_trial = False
            else:
                # Create new subscription
                new_subscription = UserSubscription(
                    user_id=user.id,
                    plan_id=transfer.plan.id,
                    status='active',
                    start_date=datetime.utcnow(),
                    end_date=datetime.utcnow() + timedelta(days=30 * payment.total_months_provided),
                    is_trial=False
                )
                db.session.add(new_subscription)
        
        db.session.commit()
        
        # Send confirmation email to user
        from app.utils.email_service import email_service
        email_service.send_subscription_activation_email(user, transfer.plan, payment)
        
        return jsonify({
            'success': True,
            'message': 'Bank transfer verified and subscription activated'
        })
        
    elif verification_status == 'rejected':
        transfer.status = 'rejected'
        transfer.verified_by = current_user.id
        transfer.verified_at = datetime.utcnow()
        transfer.admin_notes = admin_notes
        
        # Update payment status
        payment = SubscriptionPayment.query.filter_by(bank_transfer_id=transfer.id).first()
        if payment:
            payment.payment_status = 'failed'
        
        db.session.commit()
        
        # Send rejection email to user
        from app.utils.email_service import email_service
        email_service.send_bank_transfer_rejection_email(transfer.user, transfer, admin_notes)
        
        return jsonify({
            'success': True,
            'message': 'Bank transfer rejected'
        })
    
    return jsonify({'success': False, 'message': 'Invalid verification status'})

@subscription_bp.route('/pricing')
def get_pricing():
    """API endpoint to get all pricing options"""
    from app.models.subscription import SubscriptionPlan, SubscriptionPlanPricing
    
    plans = SubscriptionPlan.query.filter_by(is_active=True).all()
    pricing_data = []
    
    for plan in plans:
        plan_pricing = {
            'plan_id': plan.id,
            'plan_name': plan.name,
            'base_price': plan.price,
            'options': []
        }
        
        for pricing in plan.pricing_options:
            if pricing.is_active:
                plan_pricing['options'].append({
                    'months': pricing.months,
                    'bonus_months': pricing.bonus_months,
                    'total_price': pricing.total_price,
                    'discount_percentage': pricing.discount_percentage,
                    'total_months_provided': pricing.total_months_provided
                })
        
        pricing_data.append(plan_pricing)
    
    return jsonify(pricing_data)

@subscription_bp.route('/extend-subscription')
@login_required
def extend_subscription():
    """Show subscription extension options"""
    current_subscription = current_user.current_subscription
    
    if not current_subscription:
        flash('You do not have an active subscription to extend.', 'error')
        return redirect(url_for('subscription.plans'))
    
    from app.models.subscription import SubscriptionPlanPricing
    
    # Get pricing options for current plan
    pricing_options = SubscriptionPlanPricing.query.filter_by(
        plan_id=current_subscription.plan_id,
        is_active=True
    ).order_by(SubscriptionPlanPricing.months).all()
    
    return render_template('subscription/extend.html',
                         current_subscription=current_subscription,
                         pricing_options=pricing_options)

@subscription_bp.route('/process-extension', methods=['POST'])
@login_required
def process_extension():
    """Process subscription extension payment"""
    data = request.get_json()
    
    pricing_id = data.get('pricing_id')
    phone_number = data.get('phone_number')
    payment_method = data.get('payment_method', 'mpesa')
    
    current_subscription = current_user.current_subscription
    if not current_subscription:
        return jsonify({'success': False, 'message': 'No active subscription found'})
    
    from app.models.subscription import SubscriptionPlanPricing
    
    pricing = SubscriptionPlanPricing.query.get(pricing_id)
    if not pricing or pricing.plan_id != current_subscription.plan_id:
        return jsonify({'success': False, 'message': 'Invalid pricing option'})
    
    try:
        # Create payment record for extension
        payment = SubscriptionPayment(
            user_id=current_user.id,
            pricing_id=pricing.id,
            amount=pricing.total_price,
            months_purchased=pricing.months,
            bonus_months=pricing.bonus_months,
            payment_status='pending',
            payment_method=payment_method,
            subscription_id=current_subscription.id
        )
        
        db.session.add(payment)
        db.session.flush()
        
        if payment_method == 'mpesa':
            # Initiate M-Pesa STK push for extension
            from app.utils.mpesa import initiate_subscription_payment
            
            description = f"ChamaLink Extension - {pricing.months}M"
            response = initiate_subscription_payment(
                phone_number=phone_number,
                amount=int(pricing.total_price),
                account_reference=f"EXT-{payment.id}",
                transaction_desc=description
            )
            
            if response and response.get('success'):
                payment.mpesa_receipt_number = response.get('checkout_request_id')
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'M-Pesa prompt sent! Complete payment to extend your subscription.',
                    'payment_id': payment.id,
                    'checkout_request_id': response.get('checkout_request_id')
                })
            else:
                payment.payment_status = 'failed'
                db.session.commit()
                return jsonify({
                    'success': False,
                    'message': response.get('message', 'M-Pesa payment initiation failed')
                })
        else:
            # For other payment methods, mark as pending verification
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Extension request submitted. Please complete payment verification.',
                'payment_id': payment.id
            })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Extension payment error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Extension processing failed. Please try again.'
        })
