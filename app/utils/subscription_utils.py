"""
Subscription access control decorators and utilities
"""
from functools import wraps
from flask import redirect, url_for, flash, abort
from flask_login import current_user
from datetime import datetime


def subscription_required(f):
    """Decorator to require an active subscription"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # Super admins bypass subscription requirements
        if current_user.is_super_admin:
            return f(*args, **kwargs)
        
        subscription = current_user.current_subscription
        if not subscription or not subscription.is_active:
            flash('Your free trial has expired. Please upgrade to continue using ChamaLink.', 'warning')
            return redirect(url_for('subscription.plans'))
        
        return f(*args, **kwargs)
    return decorated_function


def feature_required(feature_name):
    """Decorator to require a specific feature"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            # Super admins have access to all features
            if current_user.is_super_admin:
                return f(*args, **kwargs)
            
            if not current_user.can_access_feature(feature_name):
                flash(f'This feature requires a higher subscription plan.', 'warning')
                return redirect(url_for('subscription.plans'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def chama_limit_check():
    """Check if user can create/join more chamas"""
    if not current_user.is_authenticated:
        return False
    
    # Super admins have unlimited chamas
    if current_user.is_super_admin:
        return True
    
    subscription = current_user.current_subscription
    if not subscription or not subscription.is_active:
        return False
    
    current_chama_count = len(current_user.chamas)
    return current_chama_count < subscription.plan.max_chamas


def check_trial_expiry():
    """Check if user's trial is about to expire"""
    if not current_user.is_authenticated:
        return None
    
    subscription = current_user.current_subscription
    if not subscription:
        return None
    
    if subscription.is_trial and subscription.days_remaining <= 7:
        return {
            'days_remaining': subscription.days_remaining,
            'expires_on': subscription.end_date.strftime('%B %d, %Y'),
            'is_trial': True
        }
    
    return None


def ensure_user_has_subscription(user):
    """Ensure user has a basic subscription (create trial if none exists)"""
    from app.models.subscription import UserSubscription, SubscriptionPlan
    from app import db
    from datetime import timedelta
    
    # Check if user already has a subscription
    existing_subscription = user.current_subscription
    if existing_subscription:
        return existing_subscription
    
    # Create a trial subscription for new users
    basic_plan = SubscriptionPlan.query.filter_by(name='basic').first()
    if not basic_plan:
        # Create basic plan if it doesn't exist
        basic_plan = SubscriptionPlan(
            name='basic',
            price=200.0,
            max_chamas=1,
            features={
                'basic_reporting': True,
                'mpesa_integration': True,
                'member_management': True,
                'meetings': True,
                'notifications': True
            },
            description='Perfect for small chamas'
        )
        db.session.add(basic_plan)
        db.session.commit()
    
    # Create 30-day trial subscription
    trial_subscription = UserSubscription(
        user_id=user.id,
        plan_id=basic_plan.id,
        status='trial',
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30),
        trial_end_date=datetime.utcnow() + timedelta(days=30),
        is_trial=True
    )
    
    db.session.add(trial_subscription)
    db.session.commit()
    
    return trial_subscription
