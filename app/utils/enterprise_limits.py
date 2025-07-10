"""
Enterprise Subscription Limits and Enforcement
"""
from functools import wraps
from flask import jsonify, current_app
from flask_login import current_user
from app.models.enterprise import EnterpriseUserSubscription, EnterpriseBillingType

def check_member_limit(f):
    """Decorator to check if user can add more members based on their subscription"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        
        # Get user's enterprise subscription
        subscription = EnterpriseUserSubscription.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).first()
        
        if not subscription:
            # Allow if no enterprise subscription (regular user)
            return f(*args, **kwargs)
        
        # Check if they can add more members
        if subscription.plan.billing_type == EnterpriseBillingType.PER_MEMBER:
            if subscription.current_members >= subscription.paid_member_limit:
                return jsonify({
                    'success': False,
                    'message': f'Member limit reached! You have paid for {subscription.paid_member_limit} members. Please upgrade your payment to add more members.',
                    'upgrade_required': True,
                    'current_members': subscription.current_members,
                    'paid_limit': subscription.paid_member_limit,
                    'cost_per_member': subscription.plan.price_per_member
                }), 403
        else:
            if subscription.current_members >= subscription.plan.max_members_per_chama:
                return jsonify({
                    'success': False,
                    'message': f'Member limit reached! Your plan allows {subscription.plan.max_members_per_chama} members. Please upgrade your plan.',
                    'upgrade_required': True
                }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def check_chama_limit(f):
    """Decorator to check if user can add more chamas based on their subscription"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        
        # Get user's enterprise subscription
        subscription = EnterpriseUserSubscription.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).first()
        
        if not subscription:
            # Allow if no enterprise subscription (regular user)
            return f(*args, **kwargs)
        
        # Check if they can add more chamas
        if not subscription.can_add_chama():
            return jsonify({
                'success': False,
                'message': f'Chama limit reached! Your plan allows {subscription.plan.max_chamas} chamas. Please upgrade your plan.',
                'upgrade_required': True
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def update_member_count(user_id, change=1):
    """Update member count for user's subscription"""
    subscription = EnterpriseUserSubscription.query.filter_by(
        user_id=user_id,
        is_active=True
    ).first()
    
    if subscription:
        subscription.current_members += change
        if subscription.current_members < 0:
            subscription.current_members = 0
        
        from app import db
        db.session.commit()
        return True
    
    return False

def update_chama_count(user_id, change=1):
    """Update chama count for user's subscription"""
    subscription = EnterpriseUserSubscription.query.filter_by(
        user_id=user_id,
        is_active=True
    ).first()
    
    if subscription:
        subscription.current_chamas += change
        if subscription.current_chamas < 0:
            subscription.current_chamas = 0
        
        from app import db
        db.session.commit()
        return True
    
    return False

def get_user_limits(user_id):
    """Get current usage and limits for a user"""
    subscription = EnterpriseUserSubscription.query.filter_by(
        user_id=user_id,
        is_active=True
    ).first()
    
    if not subscription:
        return None
    
    return subscription.get_usage_summary()

def calculate_upgrade_cost(user_id, additional_members):
    """Calculate cost to upgrade for additional members"""
    subscription = EnterpriseUserSubscription.query.filter_by(
        user_id=user_id,
        is_active=True
    ).first()
    
    if not subscription or subscription.plan.billing_type != EnterpriseBillingType.PER_MEMBER:
        return None
    
    total_members = subscription.current_members + additional_members
    required_payment = subscription.plan.calculate_monthly_cost(
        member_count=total_members,
        include_service=not subscription.service_fee_paid
    )
    
    # Subtract what they've already paid
    additional_payment = max(0, required_payment - subscription.last_payment_amount)
    
    return {
        'current_members': subscription.current_members,
        'additional_members': additional_members,
        'total_members': total_members,
        'cost_per_member': subscription.plan.price_per_member,
        'additional_payment': additional_payment,
        'total_monthly_cost': required_payment
    }
