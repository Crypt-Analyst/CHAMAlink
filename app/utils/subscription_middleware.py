"""
Subscription middleware for CHAMAlink
Enforces trial and subscription limits
"""

from flask import request, redirect, url_for, flash, g, current_app
from flask_login import current_user
from datetime import datetime
from app.models.subscription import UserSubscription, SubscriptionPlan
from functools import wraps
import re

def check_subscription_status():
    """Check current user's subscription status"""
    if not current_user.is_authenticated:
        return None
    
    # Super admin bypasses all checks
    if current_user.is_super_admin:
        return 'admin_access'
    
    # Get current subscription
    subscription = UserSubscription.query.filter_by(user_id=current_user.id).first()
    
    if not subscription:
        return 'no_subscription'
    
    now = datetime.now()
    
    # Check if trial is expired
    if subscription.is_trial and subscription.trial_end_date and subscription.trial_end_date < now:
        subscription.status = 'trial_expired'
        from app import db
        db.session.commit()
        return 'trial_expired'
    
    # Check if subscription is expired
    if subscription.end_date and subscription.end_date < now:
        subscription.status = 'expired'
        from app import db
        db.session.commit()
        return 'expired'
    
    # Check status
    if subscription.status in ['trial_expired', 'expired', 'cancelled']:
        return subscription.status
    
    return 'active'

def require_active_subscription(f):
    """Decorator to require active subscription for route access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        status = check_subscription_status()
        
        # Allow access for admin and active subscriptions
        if status in ['admin_access', 'active']:
            return f(*args, **kwargs)
        
        # Handle different expiration scenarios
        if status == 'trial_expired':
            flash('Your 30-day free trial has expired. Please upgrade to continue using CHAMAlink.', 'error')
            return redirect(url_for('subscription_new.trial_expired'))
        elif status == 'expired':
            flash('Your subscription has expired. Please renew to continue.', 'error')
            return redirect(url_for('subscription_new.subscription_expired'))
        elif status == 'no_subscription':
            flash('Please select a subscription plan to continue.', 'info')
            return redirect(url_for('subscription_new.pricing'))
        else:
            flash('Account access suspended. Please contact support.', 'error')
            return redirect(url_for('main.contact'))
    
    return decorated_function

def init_subscription_middleware(app):
    """Initialize subscription checking middleware"""
    
    @app.before_request
    def check_subscription_before_request():
        """Check subscription status before each request"""
        
        # Skip checks for certain routes
        exempt_routes = [
            'auth.login', 'auth.logout', 'auth.register', 
            'main.home', 'main.contact', 'main.demo',
            'subscription_new.pricing', 'subscription_new.trial_expired',
            'subscription_new.subscription_expired', 'subscription_new.payment',
            'static', 'feedback.submit', 'admin.'
        ]
        
        # Skip for static files and exempt routes
        if (request.endpoint and 
            (request.endpoint.startswith('static') or 
             any(request.endpoint.startswith(route) for route in exempt_routes))):
            return
        
        # Skip for non-authenticated users on public routes
        if not current_user.is_authenticated:
            return
        
        # Skip for super admin
        if current_user.is_super_admin:
            g.subscription_status = 'admin_access'
            return
        
        # Check subscription status
        status = check_subscription_status()
        g.subscription_status = status
        
        # Redirect if subscription is expired and trying to access protected resources
        if status in ['trial_expired', 'expired'] and request.endpoint:
            protected_prefixes = ['chama.', 'mpesa.', 'loans.', 'reports.', 'membership.']
            
            if any(request.endpoint.startswith(prefix) for prefix in protected_prefixes):
                if status == 'trial_expired':
                    flash('Your free trial has expired. Upgrade to continue using chamas.', 'warning')
                    return redirect(url_for('subscription_new.trial_expired'))
                else:
                    flash('Your subscription has expired. Please renew to continue.', 'warning')
                    return redirect(url_for('subscription_new.subscription_expired'))

def get_subscription_info():
    """Get current user's subscription information"""
    if not current_user.is_authenticated:
        return None
    
    if current_user.is_super_admin:
        return {
            'status': 'admin',
            'plan': 'Admin Access',
            'days_remaining': 999,
            'is_trial': False
        }
    
    subscription = UserSubscription.query.filter_by(user_id=current_user.id).first()
    if not subscription:
        return None
    
    return {
        'status': subscription.status,
        'plan': subscription.plan.name if subscription.plan else 'Unknown',
        'days_remaining': subscription.days_remaining,
        'is_trial': subscription.is_trial,
        'trial_end_date': subscription.trial_end_date,
        'end_date': subscription.end_date
    }
