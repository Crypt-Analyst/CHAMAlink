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
        from app.models import Chama
        chama = Chama.query.get_or_404(chama_id)
        if current_user not in chama.members:
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
    from app.models import Chama
    chama = Chama.query.get(chama_id)
    if not chama:
        return False
    
    # Check if user is a member
    from app.models import User
    user = User.query.get(user_id)
    return user in chama.members if user else False

def user_can_admin_chama(user_id, chama_id):
    """Check if a user can administer a specific chama"""
    role = get_user_chama_role(user_id, chama_id)
    return role in ['admin', 'creator'] if role else False
