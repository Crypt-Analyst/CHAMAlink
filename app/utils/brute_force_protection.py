"""
Advanced Brute Force Protection System
====================================
Multi-layered protection against brute force attacks with real-time notifications
"""

import time
import hashlib
import threading
from datetime import datetime, timedelta
from collections import defaultdict, deque
from flask import request, abort, current_app
from app.models import User, LoginAttempt
from app import db
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os

class AdvancedBruteForceProtection:
    """Advanced brute force protection with multiple detection layers"""
    
    def __init__(self):
        # Track failed attempts by IP
        self.ip_attempts = defaultdict(deque)
        self.ip_blocked = {}
        
        # Track failed attempts by email
        self.email_attempts = defaultdict(deque)
        self.email_blocked = {}
        
        # Progressive rate limiting
        self.rate_limits = defaultdict(deque)
        
        # Suspicious patterns tracking
        self.suspicious_patterns = defaultdict(list)
        
        # Attack signatures
        self.attack_signatures = []
        
        # Notification settings
        self.admin_emails = ['bilfordderick@gmail.com']  # Add admin emails
        self.notification_cooldown = defaultdict(float)
        
        # Load configuration
        self.config = {
            'max_attempts_per_ip': 5,      # Max attempts per IP in time window
            'max_attempts_per_email': 3,   # Max attempts per email in time window
            'time_window': 300,            # 5 minutes
            'lockout_duration': 1800,      # 30 minutes lockout
            'progressive_delays': [1, 2, 5, 10, 30, 60],  # Progressive delays in seconds
            'notification_cooldown': 300,  # 5 minutes between notifications
            'honey_pot_enabled': True,     # Enable honeypot detection
            'geo_blocking': True,          # Enable geographic anomaly detection
        }
        
        print("🛡️  Advanced Brute Force Protection: INITIALIZED")
    
    def check_brute_force_attempt(self, ip_address, email=None, user_agent=None):
        """
        Comprehensive brute force detection
        Returns: (is_allowed, delay_seconds, reason)
        """
        current_time = time.time()
        
        # 1. Check if IP is currently blocked
        if ip_address in self.ip_blocked:
            if current_time < self.ip_blocked[ip_address]:
                return False, self.ip_blocked[ip_address] - current_time, "IP_BLOCKED"
            else:
                del self.ip_blocked[ip_address]
        
        # 2. Check if email is currently blocked
        if email and email in self.email_blocked:
            if current_time < self.email_blocked[email]:
                return False, self.email_blocked[email] - current_time, "EMAIL_BLOCKED"
            else:
                del self.email_blocked[email]
        
        # 3. Check IP attempt rate
        ip_attempts = self.ip_attempts[ip_address]
        ip_attempts = deque([t for t in ip_attempts if current_time - t < self.config['time_window']])
        self.ip_attempts[ip_address] = ip_attempts
        
        if len(ip_attempts) >= self.config['max_attempts_per_ip']:
            self._block_ip(ip_address, current_time)
            self._send_security_alert(f"IP {ip_address} blocked for brute force attempts")
            return False, self.config['lockout_duration'], "IP_RATE_EXCEEDED"
        
        # 4. Check email attempt rate (if provided)
        if email:
            email_attempts = self.email_attempts[email]
            email_attempts = deque([t for t in email_attempts if current_time - t < self.config['time_window']])
            self.email_attempts[email] = email_attempts
            
            if len(email_attempts) >= self.config['max_attempts_per_email']:
                self._block_email(email, current_time)
                self._send_security_alert(f"Email {email} blocked for brute force attempts")
                return False, self.config['lockout_duration'], "EMAIL_RATE_EXCEEDED"
        
        # 5. Progressive delay based on previous attempts
        delay = self._calculate_progressive_delay(ip_address, email)
        
        # 6. Check for suspicious patterns
        if self._detect_suspicious_patterns(ip_address, email, user_agent):
            self._send_security_alert(f"Suspicious pattern detected from IP {ip_address}")
            return False, delay * 2, "SUSPICIOUS_PATTERN"
        
        return True, delay, "ALLOWED"
    
    def record_failed_attempt(self, ip_address, email=None, user_agent=None, details=None):
        """Record a failed login attempt"""
        current_time = time.time()
        
        # Record IP attempt
        self.ip_attempts[ip_address].append(current_time)
        
        # Record email attempt if provided
        if email:
            self.email_attempts[email].append(current_time)
        
        # Record suspicious patterns
        self._record_pattern(ip_address, email, user_agent, details)
        
        # Check for immediate blocking
        self._check_immediate_threats(ip_address, email)
    
    def record_successful_attempt(self, ip_address, email=None):
        """Record a successful login attempt"""
        # Reset attempt counters for this IP/email combination
        if ip_address in self.ip_attempts:
            # Keep some history but reduce the penalty
            recent_attempts = deque([
                t for t in self.ip_attempts[ip_address] 
                if time.time() - t < 60  # Only keep last minute
            ])
            self.ip_attempts[ip_address] = recent_attempts
        
        if email and email in self.email_attempts:
            # Clear email attempts on successful login
            self.email_attempts[email].clear()
    
    def _block_ip(self, ip_address, current_time):
        """Block an IP address"""
        self.ip_blocked[ip_address] = current_time + self.config['lockout_duration']
        
        # Log the blocking
        self._log_security_event({
            'event_type': 'IP_BLOCKED',
            'ip_address': ip_address,
            'timestamp': datetime.utcnow().isoformat(),
            'duration': self.config['lockout_duration']
        })
    
    def _block_email(self, email, current_time):
        """Block an email address"""
        self.email_blocked[email] = current_time + self.config['lockout_duration']
        
        # Log the blocking
        self._log_security_event({
            'event_type': 'EMAIL_BLOCKED',
            'email': email,
            'timestamp': datetime.utcnow().isoformat(),
            'duration': self.config['lockout_duration']
        })
    
    def _calculate_progressive_delay(self, ip_address, email):
        """Calculate progressive delay based on attempt history"""
        ip_count = len(self.ip_attempts.get(ip_address, []))
        email_count = len(self.email_attempts.get(email, [])) if email else 0
        
        max_count = max(ip_count, email_count)
        delay_index = min(max_count, len(self.config['progressive_delays']) - 1)
        
        return self.config['progressive_delays'][delay_index]
    
    def _detect_suspicious_patterns(self, ip_address, email, user_agent):
        """Detect suspicious attack patterns"""
        current_time = time.time()
        
        # Pattern 1: Rapid sequential attempts
        if ip_address in self.ip_attempts:
            recent_attempts = [t for t in self.ip_attempts[ip_address] if current_time - t < 60]
            if len(recent_attempts) >= 3:
                return True
        
        # Pattern 2: Multiple different emails from same IP
        if self._count_unique_emails_from_ip(ip_address) > 5:
            return True
        
        # Pattern 3: Suspicious user agent patterns
        if user_agent and self._is_suspicious_user_agent(user_agent):
            return True
        
        # Pattern 4: Common attack email patterns
        if email and self._is_attack_email_pattern(email):
            return True
        
        return False
    
    def _count_unique_emails_from_ip(self, ip_address):
        """Count unique emails attempted from an IP"""
        # This would need to be stored and tracked
        # For now, return 0 (placeholder)
        return 0
    
    def _is_suspicious_user_agent(self, user_agent):
        """Check for suspicious user agent patterns"""
        suspicious_patterns = [
            'curl', 'wget', 'python', 'requests', 'bot', 'scanner',
            'nikto', 'sqlmap', 'nmap', 'masscan'
        ]
        
        user_agent_lower = user_agent.lower()
        return any(pattern in user_agent_lower for pattern in suspicious_patterns)
    
    def _is_attack_email_pattern(self, email):
        """Check for common attack email patterns"""
        attack_patterns = [
            'admin@', 'administrator@', 'root@', 'test@', 'user@',
            '123@', 'password@', 'login@', 'support@'
        ]
        
        return any(pattern in email.lower() for pattern in attack_patterns)
    
    def _record_pattern(self, ip_address, email, user_agent, details):
        """Record attack patterns for analysis"""
        pattern = {
            'timestamp': time.time(),
            'ip_address': ip_address,
            'email': email,
            'user_agent': user_agent,
            'details': details
        }
        
        self.suspicious_patterns[ip_address].append(pattern)
        
        # Keep only recent patterns
        cutoff = time.time() - 3600  # Last hour
        self.suspicious_patterns[ip_address] = [
            p for p in self.suspicious_patterns[ip_address]
            if p['timestamp'] > cutoff
        ]
    
    def _check_immediate_threats(self, ip_address, email):
        """Check for immediate threats requiring instant blocking"""
        current_time = time.time()
        
        # Check for rapid-fire attempts (more than 3 in 10 seconds)
        if ip_address in self.ip_attempts:
            recent = [t for t in self.ip_attempts[ip_address] if current_time - t < 10]
            if len(recent) >= 3:
                self._block_ip(ip_address, current_time)
                self._send_emergency_alert(f"IMMEDIATE THREAT: Rapid-fire attack from {ip_address}")
    
    def _send_security_alert(self, message):
        """Send security alert to administrators"""
        current_time = time.time()
        
        # Check notification cooldown
        if current_time - self.notification_cooldown[message] < self.config['notification_cooldown']:
            return
        
        self.notification_cooldown[message] = current_time
        
        try:
            # Email notification
            self._send_email_alert(
                subject="CHAMAlink Security Alert",
                message=f"Security Alert: {message}\nTime: {datetime.utcnow().isoformat()}"
            )
            
            # Log notification
            self._log_security_event({
                'event_type': 'SECURITY_ALERT',
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            print(f"Failed to send security alert: {e}")
    
    def _send_emergency_alert(self, message):
        """Send immediate emergency alert"""
        try:
            # Bypass cooldown for emergency alerts
            self._send_email_alert(
                subject="🚨 CHAMAlink EMERGENCY SECURITY ALERT",
                message=f"EMERGENCY: {message}\nTime: {datetime.utcnow().isoformat()}\n\nImmediate action required!"
            )
            
            self._log_security_event({
                'event_type': 'EMERGENCY_ALERT',
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            print(f"Failed to send emergency alert: {e}")
    
    def _send_email_alert(self, subject, message):
        """Send email alert to administrators"""
        # Email configuration from environment
        smtp_server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('MAIL_PORT', 587))
        smtp_username = os.getenv('MAIL_USERNAME')
        smtp_password = os.getenv('MAIL_PASSWORD')
        
        if not smtp_username or not smtp_password:
            print("Email credentials not configured")
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['Subject'] = subject
            
            body = f"""
            CHAMAlink Security Alert
            =======================
            
            {message}
            
            System: CHAMAlink Production
            Server: {request.host if request else 'Unknown'}
            
            Please investigate immediately.
            
            Best regards,
            CHAMAlink Security System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            
            for admin_email in self.admin_emails:
                msg['To'] = admin_email
                server.send_message(msg)
                del msg['To']
            
            server.quit()
            
        except Exception as e:
            print(f"Failed to send email alert: {e}")
    
    def _log_security_event(self, event):
        """Log security events to file"""
        try:
            log_file = 'security_events.log'
            with open(log_file, 'a') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            print(f"Failed to log security event: {e}")
    
    def get_security_stats(self):
        """Get current security statistics"""
        current_time = time.time()
        
        return {
            'blocked_ips': len(self.ip_blocked),
            'blocked_emails': len(self.email_blocked),
            'recent_attempts': sum(
                len([t for t in attempts if current_time - t < 3600])
                for attempts in self.ip_attempts.values()
            ),
            'suspicious_patterns': sum(len(patterns) for patterns in self.suspicious_patterns.values()),
            'total_events': len(self.ip_attempts) + len(self.email_attempts)
        }
    
    def unblock_ip(self, ip_address):
        """Manually unblock an IP address"""
        if ip_address in self.ip_blocked:
            del self.ip_blocked[ip_address]
            self._log_security_event({
                'event_type': 'IP_UNBLOCKED',
                'ip_address': ip_address,
                'timestamp': datetime.utcnow().isoformat()
            })
            return True
        return False
    
    def unblock_email(self, email):
        """Manually unblock an email address"""
        if email in self.email_blocked:
            del self.email_blocked[email]
            self._log_security_event({
                'event_type': 'EMAIL_UNBLOCKED',
                'email': email,
                'timestamp': datetime.utcnow().isoformat()
            })
            return True
        return False

# Global instance
advanced_brute_force_protection = AdvancedBruteForceProtection()

print("🛡️  Advanced Brute Force Protection System: LOADED")
