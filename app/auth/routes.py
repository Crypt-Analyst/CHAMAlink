from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app.models.subscription import LoginAttempt, EmailVerification, TwoFactorAuth
from app.utils.email_service import email_service
from app import db
from .forms import RegistrationForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from datetime import datetime, timedelta
import secrets
import re
from app.utils.security_monitor import security_check, security_monitor

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
@security_check
def register():
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    # Get the plan from URL parameter
    plan = request.args.get('plan', 'basic')  # Default to basic
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Validate password strength
        password = form.password.data
        if not validate_password(password):
            flash('Password must be at least 6 characters long with letters and numbers.', 'danger')
            return render_template('register.html', form=form, plan=plan)
        
        # Validate names
        if not validate_name(form.username.data):
            flash('Username must contain only letters, numbers, and underscores.', 'danger')
            return render_template('register.html', form=form, plan=plan)
        
        # Check for existing user
        existing_user = User.query.filter(
            (User.email == form.email.data) | 
            (User.phone_number == form.phone_number.data) |
            (User.username == form.username.data)
        ).first()
        
        if existing_user:
            if existing_user.email == form.email.data:
                flash('Email already registered.', 'danger')
            elif existing_user.phone_number == form.phone_number.data:
                flash('Phone number already registered.', 'danger')
            else:
                flash('Username already taken.', 'danger')
            return render_template('register.html', form=form, plan=plan)

        try:
            # Get country information
            from app.utils.countries import get_country_by_code, get_currency_for_country
            country_info = get_country_by_code(form.country.data) if form.country.data else None
            
            # Create new user
            user = User(
                username=form.username.data,
                email=form.email.data,
                phone_number=form.phone_number.data,
                country_code=form.country.data if form.country.data else None,
                country_name=country_info['name'] if country_info else None,
                preferred_currency=get_currency_for_country(form.country.data) if form.country.data else 'KES',
                is_email_verified=False  # Require email verification
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush()  # Get user ID
            
            # Create trial subscription for new user
            from app.utils.subscription_utils import ensure_user_has_subscription
            ensure_user_has_subscription(user)
            
            # Create email verification token
            verification_token = secrets.token_urlsafe(32)
            verification = EmailVerification(
                user_id=user.id,
                verification_token=verification_token,
                email=user.email,
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            db.session.add(verification)
            db.session.commit()
            
            # Send verification email
            verification_url = url_for('auth.verify_email', token=verification_token, _external=True)
            email_service.send_email_verification(user, verification_token)
            
            flash('Registration successful! Please check your email to verify your account. You get a 30-day free trial!', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Registration failed: {str(e)}')
            flash('Registration failed. Please try again.', 'danger')
    else:
        # Show form validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field.title()}: {error}', 'danger')

    return render_template('register.html', form=form, plan=plan)

@auth.route('/login', methods=['GET', 'POST'])
@security_check
def login():
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        
        # Get user IP and user agent for security logging
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # Log the login attempt with enhanced security monitoring
        security_monitor.log_security_event(
            'LOGIN_ATTEMPT',
            'INFO',
            f"Login attempt for email: {email} from IP: {ip_address}"
        )
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        # Log login attempt
        login_attempt = LoginAttempt(
            user_id=user.id if user else None,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False
        )
        
        if user and user.check_password(password):
            # Check if account is locked
            if user.is_account_locked:
                flash(f'Account locked until {user.locked_until.strftime("%Y-%m-%d %H:%M")}. Please try again later.', 'danger')
                login_attempt.success = False
                db.session.add(login_attempt)
                db.session.commit()
                return render_template('login.html', form=form)
            
            # Check if email is verified
            if not user.is_email_verified:
                flash('Please verify your email address before logging in.', 'warning')
                login_attempt.success = False
                db.session.add(login_attempt)
                db.session.commit()
                return render_template('login.html', form=form)
            
            # Check if 2FA is enabled
            twofa = TwoFactorAuth.query.filter_by(user_id=user.id).first()
            if twofa and twofa.is_active:
                # Store user ID in session for 2FA verification
                session['pending_2fa_user_id'] = user.id
                login_attempt.success = True
                db.session.add(login_attempt)
                db.session.commit()
                return redirect(url_for('twofa.verify'))
            
            # Successful login without 2FA
            login_attempt.success = True
            user.reset_failed_login()  # Reset failed attempts
            login_user(user, remember=form.remember_me.data if hasattr(form, 'remember_me') else False)
            
            db.session.add(login_attempt)
            db.session.commit()
            
            flash('Login successful!', 'success')
            
            # Redirect to intended page or dashboard
            next_page = request.args.get('next')
            if next_page and url_for('main.dashboard') in next_page:
                return redirect(next_page)
            return redirect(url_for('main.dashboard'))
        else:
            # Failed login - provide specific error messages for development
            if current_app.config.get('FLASK_ENV') == 'development':
                if not user:
                    flash('Email address not found. Please check your email or register first.', 'danger')
                else:
                    # User exists but password is wrong
                    user.increment_failed_login()
                    if user.failed_login_attempts >= 3:
                        # Send account locked email
                        email_service.send_account_locked_notification(user)
                    flash('Incorrect password. Please try again.', 'danger')
            else:
                # Production - use generic message for security
                if user:
                    user.increment_failed_login()
                    if user.failed_login_attempts >= 3:
                        # Send account locked email
                        email_service.send_account_locked_notification(user)
                flash('Invalid email or password.', 'danger')
            
            login_attempt.success = False
            db.session.add(login_attempt)
            db.session.commit()
    
    return render_template('login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False
    # Check for at least one letter and one number
    has_letter = any(c.isalpha() for c in password)
    has_number = any(c.isdigit() for c in password)
    return has_letter and has_number

def validate_name(name):
    """Validate name format"""
    # Only allow letters, numbers, underscores, and hyphens
    pattern = r'^[a-zA-Z0-9_-]+$'
    return re.match(pattern, name) is not None

@auth.route('/verify-email/<token>')
def verify_email(token):
    """Verify email address"""
    verification = EmailVerification.query.filter_by(verification_token=token).first()
    
    if not verification:
        flash('Invalid verification link.', 'danger')
        return redirect(url_for('auth.login'))
    
    if verification.is_expired:
        flash('Verification link has expired. Please request a new one.', 'danger')
        return redirect(url_for('auth.login'))
    
    if verification.is_verified:
        flash('Email already verified.', 'info')
        return redirect(url_for('auth.login'))
    
    # Verify the email
    user = verification.user
    user.is_email_verified = True
    verification.is_verified = True
    verification.verified_at = datetime.utcnow()
    
    db.session.commit()
    
    flash('Email verified successfully! You can now log in.', 'success')
    return redirect(url_for('auth.login'))

@auth.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Resend email verification"""
    try:
        email = request.form.get('email')
        if not email or not email.strip():
            flash('Please provide a valid email address.', 'danger')
            return redirect(url_for('auth.login'))
        
        email = email.strip().lower()
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('No account found with that email address.', 'danger')
            return redirect(url_for('auth.login'))
        
        if user.is_email_verified:
            flash('Email already verified! You can login normally.', 'info')
            return redirect(url_for('auth.login'))
        
        # Check if a recent verification was already sent (rate limiting)
        recent_verification = EmailVerification.query.filter(
            EmailVerification.user_id == user.id,
            EmailVerification.created_at > datetime.utcnow() - timedelta(minutes=5)
        ).first()
        
        if recent_verification:
            flash('Verification email already sent recently. Please check your inbox or wait 5 minutes before requesting again.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Create new verification token
        verification_token = secrets.token_urlsafe(32)
        verification = EmailVerification(
            user_id=user.id,
            verification_token=verification_token,
            email=user.email,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.session.add(verification)
        db.session.commit()
        
        # Send verification email
        verification_url = url_for('auth.verify_email', token=verification_token, _external=True)
        email_service.send_email_verification(user, verification_token)
        
        flash('Verification email sent successfully! Please check your inbox and spam folder.', 'success')
        return redirect(url_for('auth.login'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error resending verification email: {e}")
        flash('An error occurred while sending the verification email. Please try again.', 'danger')
        return redirect(url_for('auth.login'))

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password requests"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user:
            # Generate reset token
            token = user.generate_password_reset_token()
            
            # Send password reset email
            try:
                reset_url = url_for('auth.reset_password', token=token, _external=True)
                email_service.send_password_reset(user, reset_url)
                flash('Password reset link sent to your email. Please check your inbox.', 'info')
            except Exception as e:
                current_app.logger.error(f"Failed to send password reset email: {e}")
                flash('Error sending email. Please try again later.', 'danger')
        else:
            # Don't reveal if email exists or not for security
            flash('If that email address is in our system, you will receive a password reset link.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html', form=form)

@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset with token"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # Find user with this token
    user = User.query.filter_by(password_reset_token=token).first()
    
    if not user or not user.verify_password_reset_token(token):
        flash('Invalid or expired password reset link.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        # Update password
        user.set_password(form.password.data)
        user.clear_password_reset_token()
        
        flash('Your password has been reset successfully. You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form, token=token)
