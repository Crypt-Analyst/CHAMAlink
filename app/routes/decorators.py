from functools import wraps
from flask import redirect, url_for, flash, request, abort
from flask_login import current_user
from app.models.chama import Chama
from app.models.user import User
from app import db

def chama_admin_required(f):
    """Decorator to require admin access to a chama"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        chama_id = kwargs.get('chama_id')
        if not chama_id:
            flash('Invalid chama ID', 'error')
            return redirect(url_for('main.dashboard'))
        
        chama = Chama.query.get_or_404(chama_id)
        
        # Check if user is admin or creator
        if not chama.is_admin(current_user.id):
            flash('You need admin access to perform this action.', 'error')
            return redirect(url_for('chama.detail', chama_id=chama_id))
        
        return f(*args, **kwargs)
    return decorated_function

def chama_member_required(f):
    """Decorator to require member access to a chama"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        chama_id = kwargs.get('chama_id')
        if not chama_id:
            flash('Invalid chama ID', 'error')
            return redirect(url_for('main.dashboard'))
        
        chama = Chama.query.get_or_404(chama_id)
        
        # Check if user is a member
        membership = db.session.query(chama.chama_members).filter(
            chama.chama_members.c.user_id == current_user.id,
            chama.chama_members.c.chama_id == chama_id
        ).first()
        
        if not membership:
            flash('You must be a member of this chama to access this page.', 'error')
            return redirect(url_for('main.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def chama_finance_required(f):
    """Decorator to require finance access to a chama (admin or treasurer)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        chama_id = kwargs.get('chama_id')
        if not chama_id:
            flash('Invalid chama ID', 'error')
            return redirect(url_for('main.dashboard'))
        
        chama = Chama.query.get_or_404(chama_id)
        
        # Check if user has finance access
        membership = db.session.query(chama.chama_members).filter(
            chama.chama_members.c.user_id == current_user.id,
            chama.chama_members.c.chama_id == chama_id,
            chama.chama_members.c.role.in_(['admin', 'creator', 'treasurer'])
        ).first()
        
        if not membership:
            flash('You need finance access to perform this action.', 'error')
            return redirect(url_for('chama.detail', chama_id=chama_id))
        
        return f(*args, **kwargs)
    return decorated_function
