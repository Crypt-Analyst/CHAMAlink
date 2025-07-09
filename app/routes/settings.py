from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import User
from app import db
import re

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/')
@login_required
def account_settings():
    """Account settings page"""
    return render_template('settings/account.html')

@settings_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        current_password = data.get('current_password', '').strip()
        new_password = data.get('new_password', '').strip()
        confirm_password = data.get('confirm_password', '').strip()
        
        # Validation
        if not current_password or not new_password or not confirm_password:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        # Check current password
        if not check_password_hash(current_user.password_hash, current_password):
            return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400
        
        # Check password match
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': 'New passwords do not match'}), 400
        
        # Password strength validation
        if len(new_password) < 8:
            return jsonify({'success': False, 'message': 'Password must be at least 8 characters long'}), 400
        
        if not re.search(r'[A-Za-z]', new_password) or not re.search(r'\d', new_password):
            return jsonify({'success': False, 'message': 'Password must contain both letters and numbers'}), 400
        
        # Update password
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Password changed successfully!'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@settings_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        phone_number = data.get('phone_number', '').strip()
        
        # Validation
        if not username or not email:
            return jsonify({'success': False, 'message': 'Username and email are required'}), 400
        
        # Check if username is taken by another user
        existing_user = User.query.filter(User.username == username, User.id != current_user.id).first()
        if existing_user:
            return jsonify({'success': False, 'message': 'Username is already taken'}), 400
        
        # Check if email is taken by another user
        existing_email = User.query.filter(User.email == email, User.id != current_user.id).first()
        if existing_email:
            return jsonify({'success': False, 'message': 'Email is already taken'}), 400
        
        # Check if phone number is taken by another user (if provided)
        if phone_number:
            existing_phone = User.query.filter(User.phone_number == phone_number, User.id != current_user.id).first()
            if existing_phone:
                return jsonify({'success': False, 'message': 'Phone number is already taken'}), 400
            
            # Basic phone number validation
            if not re.match(r'^\+254\d{9}$', phone_number):
                return jsonify({'success': False, 'message': 'Phone number must be in format +254XXXXXXXXX'}), 400
        
        # Email validation
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400
        
        # Update profile
        current_user.username = username
        current_user.email = email
        current_user.phone_number = phone_number if phone_number else None
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Profile updated successfully!'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@settings_bp.route('/privacy')
@login_required
def privacy_settings():
    """Privacy settings page"""
    return render_template('settings/privacy.html')

@settings_bp.route('/delete_account')
@login_required
def delete_account():
    """Account deletion page"""
    return render_template('settings/delete_account.html')

@settings_bp.route('/confirm_delete_account', methods=['POST'])
@login_required
def confirm_delete_account():
    """Confirm account deletion"""
    try:
        data = request.get_json()
        password = data.get('password', '').strip()
        confirmation = data.get('confirmation', '').strip()
        
        # Validation
        if not password:
            return jsonify({'success': False, 'message': 'Password is required'}), 400
        
        if confirmation != 'DELETE':
            return jsonify({'success': False, 'message': 'Please type DELETE to confirm'}), 400
        
        # Check password
        if not check_password_hash(current_user.password_hash, password):
            return jsonify({'success': False, 'message': 'Password is incorrect'}), 400
        
        # Check if user is creator of any chamas
        created_chamas = [chama for chama in current_user.created_chamas if chama.status == 'active']
        if created_chamas:
            chama_names = ', '.join([chama.name for chama in created_chamas])
            return jsonify({
                'success': False, 
                'message': f'You cannot delete your account while you are the creator of active chamas: {chama_names}. Please transfer ownership or deactivate these chamas first.'
            }), 400
        
        # For now, we'll just deactivate the account instead of deleting
        # In a real application, you might want to anonymize data or have a soft delete
        current_user.username = f"deleted_user_{current_user.id}"
        current_user.email = f"deleted_{current_user.id}@deleted.com"
        current_user.phone_number = None
        
        # Remove from all chamas
        current_user.chamas.clear()
        
        db.session.commit()
        
        # Logout user
        from flask_login import logout_user
        logout_user()
        
        return jsonify({'success': True, 'message': 'Account deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400
