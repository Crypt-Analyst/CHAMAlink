from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import TwoFactorAuth, TwoFactorCode
from app.utils.email_service import send_2fa_code_email
from app.utils.sms_service import send_2fa_code_sms
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
import secrets
import random

twofa_bp = Blueprint('twofa', __name__, url_prefix='/2fa')

@twofa_bp.route('/setup')
@login_required
def setup():
    """2FA setup page"""
    twofa = TwoFactorAuth.query.filter_by(user_id=current_user.id).first()
    
    if not twofa:
        # Create new 2FA record
        twofa = TwoFactorAuth(
            user_id=current_user.id,
            secret_key=pyotp.random_base32()
        )
        db.session.add(twofa)
        db.session.commit()
    
    # Generate QR code for TOTP
    totp = pyotp.TOTP(twofa.secret_key)
    qr_uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="ChamaLink"
    )
    
    # Generate QR code image
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    qr_code_data = base64.b64encode(img_buffer.getvalue()).decode()
    
    return render_template('auth/2fa_setup.html', 
                         twofa=twofa, 
                         qr_code_data=qr_code_data,
                         secret_key=twofa.secret_key)

@twofa_bp.route('/enable', methods=['POST'])
@login_required
def enable():
    """Enable 2FA method"""
    try:
        data = request.get_json()
        method = data.get('method')  # sms, email, totp
        verification_code = data.get('code')
        
        twofa = TwoFactorAuth.query.filter_by(user_id=current_user.id).first()
        
        if not twofa:
            return jsonify({'success': False, 'message': '2FA setup not found'}), 400
        
        if method == 'totp':
            # Verify TOTP code
            totp = pyotp.TOTP(twofa.secret_key)
            if not totp.verify(verification_code):
                return jsonify({'success': False, 'message': 'Invalid verification code'}), 400
            
            twofa.totp_enabled = True
            
        elif method == 'sms':
            # Verify SMS code
            code_record = TwoFactorCode.query.filter_by(
                user_id=current_user.id,
                code=verification_code,
                code_type='sms',
                is_used=False
            ).first()
            
            if not code_record or code_record.is_expired:
                return jsonify({'success': False, 'message': 'Invalid or expired code'}), 400
            
            code_record.is_used = True
            twofa.sms_enabled = True
            
        elif method == 'email':
            # Verify email code
            code_record = TwoFactorCode.query.filter_by(
                user_id=current_user.id,
                code=verification_code,
                code_type='email',
                is_used=False
            ).first()
            
            if not code_record or code_record.is_expired:
                return jsonify({'success': False, 'message': 'Invalid or expired code'}), 400
            
            code_record.is_used = True
            twofa.email_enabled = True
        
        else:
            return jsonify({'success': False, 'message': 'Invalid method'}), 400
        
        # Generate backup codes
        if not twofa.backup_codes:
            backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
            twofa.backup_codes = backup_codes
        
        twofa.is_active = True
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'{method.upper()} authentication enabled successfully',
            'backup_codes': twofa.backup_codes
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@twofa_bp.route('/disable', methods=['POST'])
@login_required
def disable():
    """Disable 2FA method"""
    try:
        data = request.get_json()
        method = data.get('method')  # sms, email, totp
        
        twofa = TwoFactorAuth.query.filter_by(user_id=current_user.id).first()
        
        if not twofa:
            return jsonify({'success': False, 'message': '2FA not found'}), 400
        
        if method == 'totp':
            twofa.totp_enabled = False
        elif method == 'sms':
            twofa.sms_enabled = False
        elif method == 'email':
            twofa.email_enabled = False
        else:
            return jsonify({'success': False, 'message': 'Invalid method'}), 400
        
        # Check if any method is still enabled
        if not (twofa.totp_enabled or twofa.sms_enabled or twofa.email_enabled):
            twofa.is_active = False
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'{method.upper()} authentication disabled successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@twofa_bp.route('/send_code', methods=['POST'])
@login_required
def send_code():
    """Send 2FA code via SMS or email"""
    try:
        data = request.get_json()
        method = data.get('method')  # sms, email
        
        if method not in ['sms', 'email']:
            return jsonify({'success': False, 'message': 'Invalid method'}), 400
        
        # Generate 6-digit code
        code = str(random.randint(100000, 999999))
        
        # Store code in database
        code_record = TwoFactorCode(
            user_id=current_user.id,
            code=code,
            code_type=method,
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        
        db.session.add(code_record)
        db.session.commit()
        
        if method == 'sms':
            # Send SMS (implement SMS service)
            success = send_2fa_code_sms(current_user.phone_number, code)
            if not success:
                return jsonify({'success': False, 'message': 'Failed to send SMS'}), 500
        
        elif method == 'email':
            # Send email
            success = send_2fa_code_email(current_user.email, code)
            if not success:
                return jsonify({'success': False, 'message': 'Failed to send email'}), 500
        
        return jsonify({
            'success': True, 
            'message': f'Verification code sent to your {method}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@twofa_bp.route('/verify')
def verify():
    """2FA verification page"""
    if 'pending_2fa_user_id' not in session:
        return redirect(url_for('auth.login'))
    
    twofa = TwoFactorAuth.query.filter_by(user_id=session['pending_2fa_user_id']).first()
    
    return render_template('auth/2fa_verify.html', twofa=twofa)

@twofa_bp.route('/verify_code', methods=['POST'])
def verify_code():
    """Verify 2FA code during login"""
    try:
        if 'pending_2fa_user_id' not in session:
            return jsonify({'success': False, 'message': 'Invalid session'}), 400
        
        data = request.get_json()
        code = data.get('code')
        method = data.get('method')  # sms, email, totp, backup
        
        user_id = session['pending_2fa_user_id']
        twofa = TwoFactorAuth.query.filter_by(user_id=user_id).first()
        
        if not twofa:
            return jsonify({'success': False, 'message': '2FA not configured'}), 400
        
        verified = False
        
        if method == 'totp':
            # Verify TOTP code
            totp = pyotp.TOTP(twofa.secret_key)
            verified = totp.verify(code)
            
        elif method == 'sms':
            # Verify SMS code
            code_record = TwoFactorCode.query.filter_by(
                user_id=user_id,
                code=code,
                code_type='sms',
                is_used=False
            ).first()
            
            if code_record and not code_record.is_expired:
                code_record.is_used = True
                verified = True
            
        elif method == 'email':
            # Verify email code
            code_record = TwoFactorCode.query.filter_by(
                user_id=user_id,
                code=code,
                code_type='email',
                is_used=False
            ).first()
            
            if code_record and not code_record.is_expired:
                code_record.is_used = True
                verified = True
                
        elif method == 'backup':
            # Verify backup code
            if twofa.backup_codes and code.upper() in twofa.backup_codes:
                backup_codes = twofa.backup_codes.copy()
                backup_codes.remove(code.upper())
                twofa.backup_codes = backup_codes
                verified = True
        
        if verified:
            # Log in user
            from flask_login import login_user
            from app.models import User
            
            user = User.query.get(user_id)
            login_user(user)
            
            # Clear session
            session.pop('pending_2fa_user_id', None)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'redirect': url_for('main.dashboard')
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid verification code'}), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@twofa_bp.route('/generate_backup_codes', methods=['POST'])
@login_required
def generate_backup_codes():
    """Generate new backup codes"""
    try:
        twofa = TwoFactorAuth.query.filter_by(user_id=current_user.id).first()
        
        if not twofa:
            return jsonify({'success': False, 'message': '2FA not configured'}), 400
        
        # Generate new backup codes
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
        twofa.backup_codes = backup_codes
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'backup_codes': backup_codes
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
