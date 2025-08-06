from functools import wraps
from flask import abort, flash, redirect, url_for, request
from flask_login import current_user

def chama_member_required(f):
    """Decorator to ensure user is a member of the chama being accessed"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        chama_id = kwargs.get('chama_id') or request.view_args.get('chama_id')
        if not chama_id:
            abort(400, "Chama ID is required")
        
        # Check if user is a member of this chama
        if not current_user.is_member_of_chama(chama_id):
            flash('You do not have permission to access this chama.', 'error')
            return redirect(url_for('main.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def chama_admin_required(f):
    """Decorator to ensure user is an admin of the chama being accessed"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        chama_id = kwargs.get('chama_id') or request.view_args.get('chama_id')
        if not chama_id:
            abort(400, "Chama ID is required")
        
        # Check if user is an admin of this chama
        from app.models import Chama, chama_members
        from app import db
        
        membership = db.session.query(chama_members).filter(
            chama_members.c.user_id == current_user.id,
            chama_members.c.chama_id == chama_id,
            chama_members.c.role.in_(['admin', 'creator'])
        ).first()
        
        if not membership:
            flash('You do not have admin permissions for this chama.', 'error')
            return redirect(url_for('main.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to ensure user is a system admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        # Check if user is a system admin or super admin
        if not (getattr(current_user, 'is_super_admin', False) or 
                getattr(current_user, 'is_admin', False) or 
                current_user.role == 'admin' or 
                current_user.role == 'super_admin'):
            flash('You do not have admin permissions.', 'error')
            return redirect(url_for('main.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def get_user_chama_role(user_id, chama_id):
    """Get the role of a user in a specific chama"""
    from app.models import chama_members
    from app import db
    
    membership = db.session.query(chama_members).filter(
        chama_members.c.user_id == user_id,
        chama_members.c.chama_id == chama_id
    ).first()
    
    return membership.role if membership else None

def user_can_access_chama(user_id, chama_id):
    """Check if a user can access a specific chama"""
    try:
        from app.models import chama_members
        from app import db
        
        # Direct database query to check membership
        membership = db.session.query(chama_members).filter(
            chama_members.c.user_id == user_id,
            chama_members.c.chama_id == chama_id
        ).first()
        
        return membership is not None
        
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Error checking chama access: user_id={user_id}, chama_id={chama_id}, error={e}")
        return False

def user_can_admin_chama(user_id, chama_id):
    """Check if a user can administer a specific chama"""
    role = get_user_chama_role(user_id, chama_id)
    return role in ['admin', 'creator'] if role else False
