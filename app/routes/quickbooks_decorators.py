from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user
from app.models import ChamaMember

def treasurer_or_admin_required(f):
    """Allow access to system admins, creators, or treasurers of the specific chama"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # System admin has full access
        if hasattr(current_user, 'is_admin') and current_user.is_admin:
            return f(*args, **kwargs)
        
        # Check chama-specific roles
        chama_id = kwargs.get('chama_id')
        if chama_id:
            membership = ChamaMember.query.filter_by(
                user_id=current_user.id,
                chama_id=chama_id
            ).first()
            
            if membership and membership.role in ['creator', 'treasurer']:
                return f(*args, **kwargs)
        
        flash('You need to be a treasurer or administrator to access this feature.', 'error')
        abort(403)
    return decorated_function

def financial_role_required(f):
    """Allow access to creator, chairperson, or treasurer for financial operations"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # System admin has full access
        if hasattr(current_user, 'is_admin') and current_user.is_admin:
            return f(*args, **kwargs)
        
        chama_id = kwargs.get('chama_id')
        if chama_id:
            membership = ChamaMember.query.filter_by(
                user_id=current_user.id,
                chama_id=chama_id
            ).first()
            
            if membership and membership.role in ['creator', 'chairperson', 'treasurer']:
                return f(*args, **kwargs)
        
        flash('You need financial management permissions to access this feature.', 'error')
        abort(403)
    return decorated_function

def secretary_or_higher_required(f):
    """Allow access to secretary level and above (secretary, treasurer, chairperson, creator)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # System admin has full access
        if hasattr(current_user, 'is_admin') and current_user.is_admin:
            return f(*args, **kwargs)
        
        chama_id = kwargs.get('chama_id')
        if chama_id:
            membership = ChamaMember.query.filter_by(
                user_id=current_user.id,
                chama_id=chama_id
            ).first()
            
            if membership and membership.role in ['creator', 'chairperson', 'treasurer', 'secretary']:
                return f(*args, **kwargs)
        
        flash('You need leadership permissions to access this feature.', 'error')
        abort(403)
    return decorated_function

def can_manage_quickbooks(user_id, chama_id=None):
    """Check if user can manage QuickBooks connections (creator/admin only)"""
    # System admin can manage all
    if hasattr(current_user, 'is_admin') and current_user.is_admin:
        return True
    
    if chama_id:
        membership = ChamaMember.query.filter_by(
            user_id=user_id,
            chama_id=chama_id
        ).first()
        
        return membership and membership.role == 'creator'
    
    return False

def can_sync_financials(user_id, chama_id):
    """Check if user can sync financial data to QuickBooks"""
    # System admin can sync all
    if hasattr(current_user, 'is_admin') and current_user.is_admin:
        return True
    
    membership = ChamaMember.query.filter_by(
        user_id=user_id,
        chama_id=chama_id
    ).first()
    
    return membership and membership.role in ['creator', 'chairperson', 'treasurer']

def can_view_quickbooks_status(user_id, chama_id):
    """Check if user can view QuickBooks connection status"""
    # System admin can view all
    if hasattr(current_user, 'is_admin') and current_user.is_admin:
        return True
    
    membership = ChamaMember.query.filter_by(
        user_id=user_id,
        chama_id=chama_id
    ).first()
    
    return membership and membership.role in ['creator', 'chairperson', 'treasurer', 'secretary']

def get_user_quickbooks_permissions(user_id, chama_id):
    """Get comprehensive QuickBooks permissions for a user in a specific chama"""
    permissions = {
        'can_connect': False,
        'can_disconnect': False,
        'can_sync': False,
        'can_view_status': False,
        'can_view_logs': False,
        'can_configure': False
    }
    
    # System admin gets all permissions
    if hasattr(current_user, 'is_admin') and current_user.is_admin:
        return {key: True for key in permissions.keys()}
    
    membership = ChamaMember.query.filter_by(
        user_id=user_id,
        chama_id=chama_id
    ).first()
    
    if not membership:
        return permissions
    
    role = membership.role
    
    if role == 'creator':
        # Creator gets all permissions
        permissions = {key: True for key in permissions.keys()}
    elif role == 'chairperson':
        permissions.update({
            'can_sync': True,
            'can_view_status': True,
            'can_view_logs': True
        })
    elif role == 'treasurer':
        permissions.update({
            'can_sync': True,
            'can_view_status': True,
            'can_view_logs': True
        })
    elif role == 'secretary':
        permissions.update({
            'can_view_status': True
        })
    
    return permissions
