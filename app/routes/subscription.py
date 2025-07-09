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
    """Subscribe to a plan"""
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    
    # Check if user already has an active subscription
    current_subscription = current_user.current_subscription
    if current_subscription and current_subscription.is_active:
        flash('You already have an active subscription.', 'info')
        return redirect(url_for('subscription.plans'))
    
    # Create new subscription with trial period
    trial_end = datetime.utcnow() + timedelta(days=30)  # 1 month trial
    subscription_end = trial_end
    
    subscription = UserSubscription(
        user_id=current_user.id,
        plan_id=plan.id,
        status='trial',
        trial_end_date=trial_end,
        end_date=subscription_end,
        is_trial=True
    )
    
    db.session.add(subscription)
    db.session.commit()
    
    # Send welcome email
    send_subscription_email(
        current_user.email,
        'subscription_welcome',
        {
            'user': current_user,
            'plan': plan,
            'trial_days': 30
        }
    )
    
    flash(f'Successfully subscribed to {plan.name} plan with 30-day free trial!', 'success')
    return redirect(url_for('main.dashboard'))

@subscription_bp.route('/pay/<int:subscription_id>')
@login_required
def pay_subscription(subscription_id):
    """Process subscription payment"""
    subscription = UserSubscription.query.get_or_404(subscription_id)
    
    # Verify ownership
    if subscription.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('subscription.plans'))
    
    # Check if payment is needed
    if subscription.status == 'active' and subscription.end_date > datetime.utcnow():
        flash('Subscription is already active.', 'info')
        return redirect(url_for('subscription.plans'))
    
    return render_template('subscription/pay.html', subscription=subscription)

@subscription_bp.route('/process_payment', methods=['POST'])
@login_required
def process_payment():
    """Process M-Pesa payment for subscription"""
    subscription_id = request.form.get('subscription_id')
    phone_number = request.form.get('phone_number')
    
    subscription = UserSubscription.query.get_or_404(subscription_id)
    
    # Verify ownership
    if subscription.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    # Validate phone number
    if not phone_number or len(phone_number) < 10:
        return jsonify({'success': False, 'message': 'Invalid phone number'})
    
    # Format phone number
    if phone_number.startswith('0'):
        phone_number = '254' + phone_number[1:]
    elif phone_number.startswith('+254'):
        phone_number = phone_number[1:]
    elif not phone_number.startswith('254'):
        phone_number = '254' + phone_number
    
    try:
        # Create payment record
        payment = SubscriptionPayment(
            user_id=current_user.id,
            subscription_id=subscription.id,
            amount=subscription.plan.price,
            payment_status='pending'
        )
        db.session.add(payment)
        db.session.commit()
        
        # Initiate M-Pesa STK push for subscription (to till 5625121)
        description = f"ChamaLink {subscription.plan.name.title()} Plan"
        response = initiate_subscription_payment(
            phone_number=phone_number,
            amount=int(subscription.plan.price),
            account_reference=f"SUB-{subscription.id}",
            transaction_desc=description
        )
        
        if response and response.get('ResponseCode') == '0':
            # Store checkout request ID for callback processing
            payment.mpesa_receipt_number = response.get('CheckoutRequestID')
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Payment request sent to your phone. Please complete the payment.',
                'checkout_request_id': response.get('CheckoutRequestID')
            })
        else:
            payment.payment_status = 'failed'
            db.session.commit()
            return jsonify({
                'success': False,
                'message': 'Payment request failed. Please try again.'
            })
            
    except Exception as e:
        current_app.logger.error(f"Subscription payment error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while processing payment'
        })

@subscription_bp.route('/callback/mpesa', methods=['POST'])
def mpesa_callback():
    """Handle M-Pesa callback for subscription payments"""
    try:
        callback_data = request.get_json()
        
        if not callback_data:
            return jsonify({'ResponseCode': '1', 'ResponseDesc': 'Invalid callback data'})
        
        # Extract callback data
        stk_callback = callback_data.get('Body', {}).get('stkCallback', {})
        result_code = stk_callback.get('ResultCode')
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        
        # Find payment record
        payment = SubscriptionPayment.query.filter_by(
            mpesa_receipt_number=checkout_request_id
        ).first()
        
        if not payment:
            current_app.logger.error(f"Payment not found for checkout request: {checkout_request_id}")
            return jsonify({'ResponseCode': '1', 'ResponseDesc': 'Payment not found'})
        
        if result_code == 0:  # Successful payment
            # Extract transaction details
            callback_metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
            mpesa_receipt = None
            
            for item in callback_metadata:
                if item.get('Name') == 'MpesaReceiptNumber':
                    mpesa_receipt = item.get('Value')
                    break
            
            # Update payment status
            payment.payment_status = 'completed'
            payment.payment_date = datetime.utcnow()
            payment.mpesa_receipt_number = mpesa_receipt or checkout_request_id
            
            # Update subscription status
            subscription = payment.subscription
            if subscription.is_trial:
                # Convert trial to active
                subscription.status = 'active'
                subscription.is_trial = False
                subscription.end_date = datetime.utcnow() + timedelta(days=30)
            else:
                # Extend subscription
                if subscription.end_date < datetime.utcnow():
                    subscription.end_date = datetime.utcnow() + timedelta(days=30)
                else:
                    subscription.end_date += timedelta(days=30)
                subscription.status = 'active'
            
            db.session.commit()
            
            # Send confirmation email
            send_subscription_email(
                subscription.user.email,
                'payment_confirmation',
                {
                    'user': subscription.user,
                    'plan': subscription.plan,
                    'payment': payment,
                    'end_date': subscription.end_date
                }
            )
            
            current_app.logger.info(f"Subscription payment completed for user {subscription.user.id}")
            
        else:  # Failed payment
            payment.payment_status = 'failed'
            db.session.commit()
            current_app.logger.error(f"Subscription payment failed for user {payment.user_id}")
        
        return jsonify({'ResponseCode': '0', 'ResponseDesc': 'Success'})
        
    except Exception as e:
        current_app.logger.error(f"Subscription callback error: {str(e)}")
        return jsonify({'ResponseCode': '1', 'ResponseDesc': 'Error processing callback'})

@subscription_bp.route('/status')
@login_required
def subscription_status():
    """Show current subscription status"""
    subscription = current_user.current_subscription
    payment_history = SubscriptionPayment.query.filter_by(
        user_id=current_user.id
    ).order_by(SubscriptionPayment.created_at.desc()).all()
    
    return render_template('subscription/status.html', 
                         subscription=subscription, 
                         payment_history=payment_history)

@subscription_bp.route('/cancel/<int:subscription_id>')
@login_required
def cancel_subscription(subscription_id):
    """Cancel subscription"""
    subscription = UserSubscription.query.get_or_404(subscription_id)
    
    # Verify ownership
    if subscription.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('subscription.status'))
    
    # Cancel subscription
    subscription.status = 'cancelled'
    subscription.auto_renew = False
    db.session.commit()
    
    # Send cancellation email
    send_subscription_email(
        current_user.email,
        'subscription_cancelled',
        {
            'user': current_user,
            'plan': subscription.plan,
            'end_date': subscription.end_date
        }
    )
    
    flash('Subscription cancelled successfully.', 'success')
    return redirect(url_for('subscription.status'))

@subscription_bp.route('/renew/<int:subscription_id>')
@login_required
def renew_subscription(subscription_id):
    """Renew subscription"""
    subscription = UserSubscription.query.get_or_404(subscription_id)
    
    # Verify ownership
    if subscription.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('subscription.status'))
    
    # Enable auto-renewal
    subscription.auto_renew = True
    if subscription.status == 'cancelled':
        subscription.status = 'active'
    
    db.session.commit()
    
    flash('Subscription renewal enabled.', 'success')
    return redirect(url_for('subscription.status'))
