"""
Advanced Security & Monitoring System for ChamaLink
This module implements comprehensive security measures and attack monitoring
"""

from flask import request, session, jsonify, current_app
from functools import wraps
import logging
import hashlib
import time
import json
from datetime import datetime, timedelta
from collections import defaultdict
import os
import re

# Import email notifier
try:
    from .email_notifier import security_notifier
except ImportError:
    security_notifier = None

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('security.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

security_logger = logging.getLogger('security')

class SecurityMonitor:
    """Advanced security monitoring and attack detection"""
    
    def __init__(self):
        # Check if we're in development/testing mode
        self.dev_mode = os.getenv('FLASK_DEBUG') == 'true' or os.getenv('TESTING') == 'True'
        
        self.attack_patterns = {
            'sql_injection': [
                r"(\%27)|(\')|(\-\-)|(\%23)|(#)",
                r"((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))",
                r"w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))",
                r"((\%27)|(\'))union",
                r"union.*select.*from",
                r"select.*from.*information_schema",
                r"drop\s+table",
                r"insert\s+into",
                r"delete\s+from"
            ],
            'xss': [
                r"<script[^>]*>.*?</script>",
                r"javascript:",
                r"on\w+\s*=",
                r"<iframe",
                r"<object",
                r"<embed",
                r"eval\s*\(",
                r"document\.cookie",
                r"document\.write"
            ],
            'path_traversal': [
                r"\.\./",
                r"\.\.\\",
                r"etc/passwd",
                r"etc\\passwd",
                r"windows/system32",
                r"proc/self/environ"
            ],
            'command_injection': [
                r";\s*cat\s+",
                r";\s*ls\s+",
                r";\s*dir\s+",
                r";\s*rm\s+",
                r";\s*del\s+",
                r"\|\s*cat\s+",
                r"\|\s*ls\s+",
                r"`.*`",
                r"\$\(.*\)"
            ]
        }
        
        self.suspicious_user_agents = [
            'sqlmap', 'nikto', 'w3af', 'burp', 'nmap', 'masscan',
            'zap', 'gobuster', 'dirb', 'curl', 'wget', 
            'scanner', 'bot', 'crawler', 'exploit', 'hack'
        ]
        
        # Allow legitimate tools for testing and development
        self.allowed_automated_agents = [
            'python-requests', 'python/3', 'pytest', 'selenium', 'postman'
        ]
        
        self.rate_limits = defaultdict(list)
        self.blocked_ips = set()
        self.failed_attempts = defaultdict(int)
        
    def get_client_info(self):
        """Get comprehensive client information"""
        return {
            'ip': request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR')),
            'user_agent': request.headers.get('User-Agent', ''),
            'referer': request.headers.get('Referer', ''),
            'method': request.method,
            'url': request.url,
            'endpoint': request.endpoint,
            'timestamp': datetime.now().isoformat(),
            'headers': dict(request.headers),
            'form_data': request.form.to_dict() if request.form else {},
            'json_data': request.get_json() if request.is_json else {},
            'args': request.args.to_dict()
        }
    
    def detect_attack_patterns(self, data_to_check):
        """Detect known attack patterns in request data"""
        threats_found = []
        
        # Convert data to string for pattern matching
        if isinstance(data_to_check, dict):
            check_string = json.dumps(data_to_check).lower()
        else:
            check_string = str(data_to_check).lower()
        
        for attack_type, patterns in self.attack_patterns.items():
            for pattern in patterns:
                if re.search(pattern, check_string, re.IGNORECASE):
                    threats_found.append({
                        'type': attack_type,
                        'pattern': pattern,
                        'matched_text': check_string[:100] + '...' if len(check_string) > 100 else check_string
                    })
        
        return threats_found
    
    def check_rate_limiting(self, ip, max_requests=100, time_window=3600):
        """Implement rate limiting"""
        current_time = time.time()
        
        # Clean old entries
        self.rate_limits[ip] = [
            timestamp for timestamp in self.rate_limits[ip]
            if current_time - timestamp < time_window
        ]
        
        # Check if rate limit exceeded
        if len(self.rate_limits[ip]) >= max_requests:
            return False
        
        # Add current request
        self.rate_limits[ip].append(current_time)
        return True
    
    def is_suspicious_user_agent(self, user_agent):
        """Check for suspicious user agents with better detection"""
        if not user_agent:
            return True
        
        user_agent_lower = user_agent.lower()
        
        # First check if it's an allowed automated agent
        for allowed in self.allowed_automated_agents:
            if allowed in user_agent_lower:
                return False
        
        # Then check against suspicious patterns
        for suspicious in self.suspicious_user_agents:
            if suspicious in user_agent_lower:
                # Additional check for legitimate python usage
                if suspicious == 'python' and any(allowed in user_agent_lower for allowed in self.allowed_automated_agents):
                    return False
                return True
        
        return False
    
    def log_security_event(self, event_type, severity, details):
        """Log security events with detailed information"""
        client_info = self.get_client_info()
        
        security_event = {
            'event_type': event_type,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            'client_info': client_info,
            'details': details
        }
        
        # Log to file
        security_logger.warning(f"SECURITY EVENT: {json.dumps(security_event, indent=2)}")
        
        # Send notification for high severity events
        if severity in ['HIGH', 'CRITICAL']:
            self.send_security_notification(security_event)
        
        return security_event
    
    def send_security_notification(self, event):
        """Send immediate notification for critical security events"""
        # In production, you would integrate with:
        # - Email notifications
        # - Slack/Teams webhooks
        # - SMS alerts
        # - Security dashboard
        
        notification_message = f"""
*** CRITICAL SECURITY ALERT ***

Event: {event['event_type']}
Severity: {event['severity']}
Time: {event['timestamp']}
IP: {event['client_info']['ip']}
User Agent: {event['client_info']['user_agent']}
URL: {event['client_info']['url']}

Details: {event['details']}

Take immediate action to investigate this potential security threat.
        """
        
        # Send email notification for high severity events
        if security_notifier and event['severity'] in ['HIGH', 'CRITICAL']:
            try:
                event_details = {
                    'ip_address': event['client_info']['ip'],
                    'user_agent': event['client_info']['user_agent'],
                    'path': event['client_info']['url'],
                    'description': event['details'],
                    'timestamp': event['timestamp'],
                    'location': event['client_info'].get('location', 'Unknown'),
                    'device_info': event['client_info'].get('device_info', 'Unknown')
                }
                
                if event['severity'] == 'CRITICAL':
                    security_notifier.send_breach_notification({
                        'type': event['event_type'],
                        'description': event['details'],
                        'vector': 'Web Application',
                        'scope': 'Under Investigation',
                        'data_types': 'User Data, Session Data'
                    })
                else:
                    security_notifier.send_security_alert(
                        event_type=event['event_type'],
                        severity=event['severity'].lower(),
                        details=event_details
                    )
            except Exception as e:
                security_logger.error(f"Failed to send email notification: {str(e)}")
        
        # For now, also print to console
        print(notification_message)
        
        # Log to special alert file
        with open('security_alerts.log', 'a') as f:
            f.write(f"{datetime.now().isoformat()}: {notification_message}\n\n")

# Global security monitor instance
security_monitor = SecurityMonitor()

def security_check(f):
    """Decorator for comprehensive security checking"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_info = security_monitor.get_client_info()
        ip = client_info['ip']
        
        # In development mode, be less restrictive
        if security_monitor.dev_mode:
            # Only block obvious attacks, allow testing
            all_data = {
                **client_info['form_data'],
                **client_info['json_data'],
                **client_info['args'],
                'url': client_info['url'],
                'user_agent': client_info['user_agent']
            }
            
            threats = security_monitor.detect_attack_patterns(all_data)
            if threats:
                # Only block if it's a serious attack pattern
                serious_threats = [t for t in threats if t['type'] in ['sql_injection', 'command_injection']]
                if serious_threats:
                    security_monitor.log_security_event(
                        'ATTACK_PATTERN_DETECTED',
                        'HIGH',
                        f"Serious attack patterns detected in dev mode: {serious_threats}"
                    )
                    return jsonify({'error': 'Malicious request detected'}), 400
            
            return f(*args, **kwargs)
        
        # Production mode - full security checks
        # Check if IP is blocked
        if ip in security_monitor.blocked_ips:
            security_monitor.log_security_event(
                'BLOCKED_IP_ACCESS',
                'HIGH',
                f"Blocked IP {ip} attempted to access {request.url}"
            )
            return jsonify({'error': 'Access denied'}), 403
        
        # Rate limiting (more lenient in dev)
        max_requests = 200 if security_monitor.dev_mode else 100
        if not security_monitor.check_rate_limiting(ip, max_requests=max_requests):
            security_monitor.log_security_event(
                'RATE_LIMIT_EXCEEDED',
                'MEDIUM',
                f"Rate limit exceeded for IP {ip}"
            )
            return jsonify({'error': 'Too many requests'}), 429
        
        # Check suspicious user agent (skip in dev mode for some agents)
        if not security_monitor.dev_mode and security_monitor.is_suspicious_user_agent(client_info['user_agent']):
            security_monitor.log_security_event(
                'SUSPICIOUS_USER_AGENT',
                'MEDIUM',
                f"Suspicious user agent: {client_info['user_agent']}"
            )
        
        # Check for attack patterns in all request data
        all_data = {
            **client_info['form_data'],
            **client_info['json_data'],
            **client_info['args'],
            'url': client_info['url'],
            'user_agent': client_info['user_agent']
        }
        
        threats = security_monitor.detect_attack_patterns(all_data)
        if threats:
            security_monitor.log_security_event(
                'ATTACK_PATTERN_DETECTED',
                'CRITICAL',
                f"Attack patterns detected: {threats}"
            )
            
            # Block IP after multiple attack attempts
            security_monitor.failed_attempts[ip] += 1
            if security_monitor.failed_attempts[ip] >= 3:
                security_monitor.blocked_ips.add(ip)
                security_monitor.log_security_event(
                    'IP_BLOCKED',
                    'CRITICAL',
                    f"IP {ip} blocked after multiple attack attempts"
                )
            
            return jsonify({'error': 'Malicious request detected'}), 400
        
        # Log normal request for monitoring
        security_monitor.log_security_event(
            'NORMAL_REQUEST',
            'INFO',
            f"Normal request to {request.endpoint}"
        )
        
        return f(*args, **kwargs)
    
    return decorated_function

def init_security(app):
    """Initialize security monitoring for Flask app"""
    
    @app.before_request
    def security_before_request():
        # Apply security checks to all requests
        if request.endpoint and not request.endpoint.startswith('static'):
            client_info = security_monitor.get_client_info()
            ip = client_info['ip']
            
            # Basic security checks on every request
            if ip in security_monitor.blocked_ips:
                security_monitor.log_security_event(
                    'BLOCKED_IP_ACCESS',
                    'HIGH',
                    f"Blocked IP {ip} attempted to access {request.url}"
                )
                return jsonify({'error': 'Access denied'}), 403
    
    @app.after_request
    def security_after_request(response):
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; font-src 'self' https://cdnjs.cloudflare.com; img-src 'self' data: https:;"
        
        return response
    
    return app
