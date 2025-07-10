"""
Enterprise Billing Routes
Handles SACCO/NGO billing, member limits, and payment processing
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.enterprise import (
    EnterpriseUserSubscription, 
    EnterpriseSubscriptionPlan, 
    EnterpriseSubscriptionPayment,
    PlanType,
    EnterpriseBillingType
)
from app.utils.enterprise_limits import (
    get_user_limits, 
    calculate_upgrade_cost,
    update_member_count
)

enterprise_bp = Blueprint('enterprise', __name__, url_prefix='/enterprise')

@enterprise_bp.route('/billing')
@login_required
def billing_dashboard():
    """Enterprise billing dashboard"""
    subscription = EnterpriseUserSubscription.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).first()
    
    if not subscription:
        # Show available enterprise plans
        plans = EnterpriseSubscriptionPlan.query.filter_by(is_active=True).all()
        return render_template('enterprise/select_plan.html', plans=plans)
    
    usage_summary = subscription.get_usage_summary()
    recent_payments = EnterpriseSubscriptionPayment.query.filter_by(
        subscription_id=subscription.id
    ).order_by(EnterpriseSubscriptionPayment.payment_date.desc()).limit(10).all()
    
    return render_template('enterprise/billing_dashboard.html', 
                         subscription=subscription,
                         usage_summary=usage_summary,
                         recent_payments=recent_payments)

@enterprise_bp.route('/calculate-cost', methods=['POST'])
@login_required
def calculate_cost():
    """Calculate cost for member count"""
    data = request.get_json()
    member_count = int(data.get('member_count', 0))
    include_service = data.get('include_service', False)
    training_days = int(data.get('training_days', 0))
    
    # Get Enterprise plan (which now includes SACCO/NGO features)
    plan = EnterpriseSubscriptionPlan.query.filter_by(
        plan_type=PlanType.ENTERPRISE,
        is_active=True
    ).first()
    
    if not plan:
        return jsonify({'success': False, 'message': 'Enterprise plan not available'}), 400
    
    cost = plan.calculate_monthly_cost(
        member_count=member_count,
        include_service=include_service,
        training_days=training_days
    )
    
    breakdown = {
        'member_cost': member_count * plan.price_per_member,
        'service_fee': plan.base_service_fee if include_service else 0,
        'training_cost': training_days * plan.training_fee_per_day,
        'total_cost': cost
    }
    
    return jsonify({
        'success': True,
        'cost': cost,
        'breakdown': breakdown,
        'member_count': member_count,
        'cost_per_member': plan.price_per_member
    })

@enterprise_bp.route('/upgrade-members', methods=['POST'])
@login_required
def upgrade_members():
    """Upgrade to support more members"""
    data = request.get_json()
    additional_members = int(data.get('additional_members', 0))
    
    if additional_members <= 0:
        return jsonify({'success': False, 'message': 'Invalid member count'}), 400
    
    upgrade_info = calculate_upgrade_cost(current_user.id, additional_members)
    
    if not upgrade_info:
        return jsonify({'success': False, 'message': 'Unable to calculate upgrade cost'}), 400
    
    return jsonify({
        'success': True,
        'upgrade_info': upgrade_info
    })

@enterprise_bp.route('/process-payment', methods=['POST'])
@login_required
def process_payment():
    """Process enterprise payment (M-Pesa integration would go here)"""
    data = request.get_json()
    member_count = int(data.get('member_count', 0))
    include_service = data.get('include_service', False)
    training_days = int(data.get('training_days', 0))
    payment_method = data.get('payment_method', 'mpesa')
    
    # Get or create subscription
    subscription = EnterpriseUserSubscription.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).first()
    
    if not subscription:
        # Create new Enterprise subscription (with SACCO/NGO features)
        plan = EnterpriseSubscriptionPlan.query.filter_by(
            plan_type=PlanType.ENTERPRISE,
            is_active=True
        ).first()
        
        if not plan:
            return jsonify({'success': False, 'message': 'Enterprise plan not available'}), 400
        
        subscription = EnterpriseUserSubscription(
            user_id=current_user.id,
            plan_id=plan.id,
            payment_method=payment_method
        )
        db.session.add(subscription)
        db.session.flush()
    
    # Calculate payment amount
    payment_amount = subscription.plan.calculate_monthly_cost(
        member_count=member_count,
        include_service=include_service,
        training_days=training_days
    )
    
    # Update subscription limits
    subscription.update_member_limit_from_payment(payment_amount)
    subscription.service_fee_paid = include_service
    subscription.training_days_purchased = training_days
    
    # Create payment record
    payment = EnterpriseSubscriptionPayment(
        subscription_id=subscription.id,
        amount=payment_amount,
        currency='KES',
        payment_method=payment_method,
        status='completed',  # In real app, this would be 'pending' until M-Pesa confirms
        description=f'Payment for {member_count} members'
    )
    
    if include_service:
        payment.description += f' + service fee'
    
    if training_days > 0:
        payment.description += f' + {training_days} training days'
    
    db.session.add(payment)
    db.session.commit()
    
    # TODO: Integrate with M-Pesa API here
    # For now, we'll simulate successful payment
    
    return jsonify({
        'success': True,
        'message': f'Payment successful! Your organization can now support {member_count} members.',
        'payment_amount': payment_amount,
        'member_limit': subscription.paid_member_limit,
        'payment_id': payment.id
    })

@enterprise_bp.route('/usage-status')
@login_required
def usage_status():
    """Get current usage status"""
    limits = get_user_limits(current_user.id)
    
    if not limits:
        return jsonify({
            'success': False,
            'message': 'No enterprise subscription found'
        }), 404
    
    return jsonify({
        'success': True,
        'usage': limits
    })

@enterprise_bp.route('/add-member', methods=['POST'])
@login_required
def add_member():
    """Add a member (with limit checking)"""
    data = request.get_json()
    
    subscription = EnterpriseUserSubscription.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).first()
    
    if subscription and not subscription.can_add_member():
        if subscription.plan.billing_type == EnterpriseBillingType.PER_MEMBER:
            return jsonify({
                'success': False,
                'message': f'Member limit reached! You have paid for {subscription.paid_member_limit} members.',
                'upgrade_required': True,
                'current_members': subscription.current_members,
                'paid_limit': subscription.paid_member_limit,
                'cost_per_additional_member': subscription.plan.price_per_member
            }), 403
    
    # TODO: Add the actual member to the chama here
    # For now, just update the count
    if subscription:
        update_member_count(current_user.id, 1)
    
    return jsonify({
        'success': True,
        'message': 'Member added successfully',
        'current_members': subscription.current_members + 1 if subscription else 1
    })

@enterprise_bp.route('/plans')
def view_plans():
    """View available enterprise plans"""
    plans = EnterpriseSubscriptionPlan.query.filter_by(is_active=True).all()
    return render_template('enterprise/plans.html', plans=plans)
