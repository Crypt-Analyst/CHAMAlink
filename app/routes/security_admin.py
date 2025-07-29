"""
Security Dashboard and Monitoring Routes
======================================
Admin routes for monitoring and managing security threats
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.utils.brute_force_protection import advanced_brute_force_protection
from app.models import User, LoginAttempt
from app import db
from datetime import datetime, timedelta
import json

security_admin = Blueprint('security_admin', __name__, url_prefix='/admin/security')

@security_admin.before_request
@login_required
def check_admin():
    """Ensure only admins can access security routes"""
    if not current_user.is_authenticated or current_user.role != 'super_admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))

@security_admin.route('/dashboard')
def dashboard():
    """Security monitoring dashboard"""
    
    # Get security statistics
    stats = advanced_brute_force_protection.get_security_stats()
    
    # Get recent security events (last 24 hours)
    recent_attempts = LoginAttempt.query.filter(
        LoginAttempt.timestamp > datetime.utcnow() - timedelta(hours=24)
    ).order_by(LoginAttempt.timestamp.desc()).limit(50).all()
    
    # Analyze patterns
    failed_attempts = [attempt for attempt in recent_attempts if not attempt.success]
    ip_analysis = {}
    email_analysis = {}
    
    for attempt in failed_attempts:
        ip = attempt.ip_address
        email = attempt.email
        
        if ip not in ip_analysis:
            ip_analysis[ip] = {'count': 0, 'emails': set(), 'latest': attempt.timestamp}
        ip_analysis[ip]['count'] += 1
        ip_analysis[ip]['emails'].add(email)
        
        if email not in email_analysis:
            email_analysis[email] = {'count': 0, 'ips': set(), 'latest': attempt.timestamp}
        email_analysis[email]['count'] += 1
        email_analysis[email]['ips'].add(ip)
    
    # Sort by most suspicious
    suspicious_ips = sorted(
        [(ip, data) for ip, data in ip_analysis.items()],
        key=lambda x: (x[1]['count'], len(x[1]['emails'])),
        reverse=True
    )[:10]
    
    suspicious_emails = sorted(
        [(email, data) for email, data in email_analysis.items()],
        key=lambda x: (x[1]['count'], len(x[1]['ips'])),
        reverse=True
    )[:10]
    
    return render_template('admin/security_dashboard.html',
                         stats=stats,
                         recent_attempts=recent_attempts[:20],
                         suspicious_ips=suspicious_ips,
                         suspicious_emails=suspicious_emails)

@security_admin.route('/blocked-ips')
def blocked_ips():
    """View and manage blocked IP addresses"""
    blocked_ips = {}
    
    # Get currently blocked IPs from the protection system
    current_time = time.time()
    for ip, block_time in advanced_brute_force_protection.ip_blocked.items():
        if block_time > current_time:
            blocked_ips[ip] = {
                'blocked_until': datetime.fromtimestamp(block_time),
                'remaining_seconds': int(block_time - current_time)
            }
    
    return render_template('admin/blocked_ips.html', blocked_ips=blocked_ips)

@security_admin.route('/unblock-ip', methods=['POST'])
def unblock_ip():
    """Unblock an IP address"""
    ip_address = request.form.get('ip_address')
    
    if not ip_address:
        flash('IP address is required.', 'danger')
        return redirect(url_for('security_admin.blocked_ips'))
    
    if advanced_brute_force_protection.unblock_ip(ip_address):
        flash(f'IP address {ip_address} has been unblocked.', 'success')
    else:
        flash(f'IP address {ip_address} was not blocked.', 'info')
    
    return redirect(url_for('security_admin.blocked_ips'))

@security_admin.route('/blocked-emails')
def blocked_emails():
    """View and manage blocked email addresses"""
    blocked_emails = {}
    
    # Get currently blocked emails from the protection system
    current_time = time.time()
    for email, block_time in advanced_brute_force_protection.email_blocked.items():
        if block_time > current_time:
            blocked_emails[email] = {
                'blocked_until': datetime.fromtimestamp(block_time),
                'remaining_seconds': int(block_time - current_time)
            }
    
    return render_template('admin/blocked_emails.html', blocked_emails=blocked_emails)

@security_admin.route('/unblock-email', methods=['POST'])
def unblock_email():
    """Unblock an email address"""
    email = request.form.get('email')
    
    if not email:
        flash('Email address is required.', 'danger')
        return redirect(url_for('security_admin.blocked_emails'))
    
    if advanced_brute_force_protection.unblock_email(email):
        flash(f'Email {email} has been unblocked.', 'success')
    else:
        flash(f'Email {email} was not blocked.', 'info')
    
    return redirect(url_for('security_admin.blocked_emails'))

@security_admin.route('/api/stats')
def api_stats():
    """API endpoint for real-time security statistics"""
    stats = advanced_brute_force_protection.get_security_stats()
    
    # Add recent activity
    recent_attempts = LoginAttempt.query.filter(
        LoginAttempt.timestamp > datetime.utcnow() - timedelta(minutes=5)
    ).count()
    
    stats['recent_activity'] = recent_attempts
    stats['timestamp'] = datetime.utcnow().isoformat()
    
    return jsonify(stats)

@security_admin.route('/security-events')
def security_events():
    """View detailed security events log"""
    
    # Read security events from log file
    events = []
    try:
        with open('security_events.log', 'r') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    events.append(event)
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        pass
    
    # Sort by timestamp (most recent first)
    events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Paginate results
    page = request.args.get('page', 1, type=int)
    per_page = 50
    start = (page - 1) * per_page
    end = start + per_page
    
    paginated_events = events[start:end]
    total_events = len(events)
    
    return render_template('admin/security_events.html',
                         events=paginated_events,
                         page=page,
                         per_page=per_page,
                         total=total_events)

@security_admin.route('/security-config')
def security_config():
    """View and manage security configuration"""
    config = advanced_brute_force_protection.config
    return render_template('admin/security_config.html', config=config)

@security_admin.route('/update-config', methods=['POST'])
def update_config():
    """Update security configuration"""
    
    try:
        # Update configuration values
        config = advanced_brute_force_protection.config
        
        config['max_attempts_per_ip'] = int(request.form.get('max_attempts_per_ip', 5))
        config['max_attempts_per_email'] = int(request.form.get('max_attempts_per_email', 3))
        config['time_window'] = int(request.form.get('time_window', 300))
        config['lockout_duration'] = int(request.form.get('lockout_duration', 1800))
        config['notification_cooldown'] = int(request.form.get('notification_cooldown', 300))
        
        flash('Security configuration updated successfully.', 'success')
        
    except ValueError as e:
        flash(f'Invalid configuration value: {e}', 'danger')
    except Exception as e:
        flash(f'Error updating configuration: {e}', 'danger')
    
    return redirect(url_for('security_admin.security_config'))

print("🛡️  Security Admin Dashboard: LOADED")
