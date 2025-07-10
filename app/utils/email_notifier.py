"""
Email notification system for security events
"""

import smtplib
import json
from datetime import datetime
from flask import current_app
import logging

# Configure email logger
email_logger = logging.getLogger('email_notifications')

class SecurityEmailNotifier:
    """Handles email notifications for security events"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.smtp_server = app.config.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = app.config.get('SMTP_PORT', 587)
        self.smtp_username = app.config.get('SMTP_USERNAME', '')
        self.smtp_password = app.config.get('SMTP_PASSWORD', '')
        self.admin_emails = app.config.get('SECURITY_ADMIN_EMAILS', ['admin@chamalink.com'])
        self.from_email = app.config.get('FROM_EMAIL', 'security@chamalink.com')
    
    def send_security_alert(self, event_type, severity, details, user_info=None):
        """Send security alert email to administrators"""
        try:
            subject = f"🚨 ChamaLink Security Alert - {event_type.upper()} ({severity})"
            
            # Create email content
            html_content = self._create_security_email_template(
                event_type, severity, details, user_info
            )
            
            # Send to all admin emails
            for admin_email in self.admin_emails:
                self._send_email(admin_email, subject, html_content)
            
            email_logger.info(f"Security alert sent for {event_type} - Severity: {severity}")
            return True
            
        except Exception as e:
            email_logger.error(f"Failed to send security alert: {str(e)}")
            return False
    
    def send_breach_notification(self, breach_details, affected_users=None):
        """Send data breach notification"""
        try:
            subject = "🔴 CRITICAL: Security Breach Detected - ChamaLink"
            
            html_content = self._create_breach_email_template(breach_details, affected_users)
            
            # Send to all admin emails with high priority
            for admin_email in self.admin_emails:
                self._send_email(admin_email, subject, html_content, priority='high')
            
            email_logger.critical(f"Breach notification sent: {breach_details.get('type', 'Unknown')}")
            return True
            
        except Exception as e:
            email_logger.error(f"Failed to send breach notification: {str(e)}")
            return False
    
    def send_suspicious_activity_alert(self, activity_details):
        """Send alert for suspicious activity patterns"""
        try:
            subject = f"⚠️ Suspicious Activity Detected - ChamaLink"
            
            html_content = self._create_suspicious_activity_template(activity_details)
            
            # Send to admin emails
            for admin_email in self.admin_emails:
                self._send_email(admin_email, subject, html_content)
            
            email_logger.warning(f"Suspicious activity alert sent: {activity_details.get('pattern', 'Unknown')}")
            return True
            
        except Exception as e:
            email_logger.error(f"Failed to send suspicious activity alert: {str(e)}")
            return False
    
    def _send_email(self, to_email, subject, html_content, priority='normal'):
        """Send email using SMTP - simplified version"""
        try:
            # For now, just log the email content since SMTP setup may not be configured
            email_logger.info(f"EMAIL TO: {to_email}")
            email_logger.info(f"SUBJECT: {subject}")
            email_logger.info(f"PRIORITY: {priority}")
            email_logger.info(f"CONTENT: {html_content[:200]}...")
            
            # In production, implement proper SMTP sending here
            # This simplified version just logs the email for demonstration
            
            return True
            
        except Exception as e:
            email_logger.error(f"Email error sending to {to_email}: {str(e)}")
            return False
    
    def _create_security_email_template(self, event_type, severity, details, user_info):
        """Create HTML email template for security alerts"""
        severity_colors = {
            'low': '#28a745',
            'medium': '#ffc107', 
            'high': '#fd7e14',
            'critical': '#dc3545'
        }
        
        color = severity_colors.get(severity.lower(), '#6c757d')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Security Alert - ChamaLink</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 24px;">🚨 Security Alert</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">ChamaLink Security Monitoring System</p>
            </div>
            
            <!-- Alert Details -->
            <div style="background: #fff; border: 1px solid #dee2e6; padding: 30px; border-radius: 0 0 10px 10px;">
                
                <!-- Severity Badge -->
                <div style="text-align: center; margin-bottom: 30px;">
                    <span style="background: {color}; color: white; padding: 8px 20px; border-radius: 20px; font-weight: bold; font-size: 16px;">
                        {severity.upper()} SEVERITY
                    </span>
                </div>
                
                <!-- Event Info -->
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="margin: 0 0 15px 0; color: #495057;">Event Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; width: 30%;">Event Type:</td>
                            <td style="padding: 8px 0;">{event_type}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Timestamp:</td>
                            <td style="padding: 8px 0;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">IP Address:</td>
                            <td style="padding: 8px 0;">{details.get('ip_address', 'Unknown')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">User Agent:</td>
                            <td style="padding: 8px 0; word-break: break-all;">{details.get('user_agent', 'Unknown')}</td>
                        </tr>
                    </table>
                </div>
                
                <!-- Additional Details -->
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h4 style="margin: 0 0 15px 0; color: #856404;">Additional Information</h4>
                    <p style="margin: 0; color: #856404;">{details.get('description', 'No additional details available.')}</p>
                    
                    {f'''
                    <div style="margin-top: 15px;">
                        <strong>Location:</strong> {details.get('location', 'Unknown')}<br>
                        <strong>Device:</strong> {details.get('device_info', 'Unknown')}<br>
                        <strong>Request Path:</strong> {details.get('path', 'Unknown')}
                    </div>
                    ''' if details.get('location') else ''}
                </div>
                
                <!-- User Information -->
                {f'''
                <div style="background: #d1ecf1; border: 1px solid #bee5eb; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h4 style="margin: 0 0 15px 0; color: #0c5460;">Affected User</h4>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 5px 0; font-weight: bold; width: 30%;">User ID:</td>
                            <td style="padding: 5px 0;">{user_info.get('id', 'N/A')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 5px 0; font-weight: bold;">Email:</td>
                            <td style="padding: 5px 0;">{user_info.get('email', 'N/A')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 5px 0; font-weight: bold;">Last Login:</td>
                            <td style="padding: 5px 0;">{user_info.get('last_login', 'N/A')}</td>
                        </tr>
                    </table>
                </div>
                ''' if user_info else ''}
                
                <!-- Actions Taken -->
                <div style="background: #d4edda; border: 1px solid #c3e6cb; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h4 style="margin: 0 0 15px 0; color: #155724;">Automatic Actions Taken</h4>
                    <ul style="margin: 0; padding-left: 20px; color: #155724;">
                        <li>Event logged to security system</li>
                        <li>Administrators notified via email</li>
                        {f'<li>IP address {details.get("ip_address")} temporarily blocked</li>' if details.get('ip_blocked') else ''}
                        {f'<li>User account flagged for review</li>' if user_info else ''}
                    </ul>
                </div>
                
                <!-- Call to Action -->
                <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                    <h4 style="margin: 0 0 15px 0;">Recommended Actions</h4>
                    <p style="margin: 0 0 20px 0;">Please review this security event and take appropriate action if necessary.</p>
                    <a href="https://chamalink.com/security-dashboard" 
                       style="background: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        View Security Dashboard
                    </a>
                </div>
                
            </div>
            
            <!-- Footer -->
            <div style="text-align: center; padding: 20px; color: #6c757d; font-size: 14px;">
                <p style="margin: 0;">This is an automated security notification from ChamaLink.</p>
                <p style="margin: 5px 0 0 0;">© 2024 ChamaLink. All rights reserved.</p>
            </div>
            
        </body>
        </html>
        """
        
        return html
    
    def _create_breach_email_template(self, breach_details, affected_users):
        """Create HTML template for breach notifications"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>CRITICAL: Security Breach - ChamaLink</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            
            <!-- Critical Header -->
            <div style="background: #dc3545; padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 26px;">🔴 CRITICAL SECURITY BREACH</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 16px;">Immediate Action Required</p>
            </div>
            
            <!-- Breach Details -->
            <div style="background: #fff; border: 2px solid #dc3545; padding: 30px; border-radius: 0 0 10px 10px;">
                
                <!-- Alert Banner -->
                <div style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 20px; border-radius: 8px; margin-bottom: 30px; text-align: center;">
                    <h2 style="margin: 0; color: #721c24; font-size: 20px;">SECURITY BREACH DETECTED</h2>
                    <p style="margin: 10px 0 0 0; color: #721c24;">This requires immediate attention from the security team.</p>
                </div>
                
                <!-- Breach Information -->
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="margin: 0 0 15px 0; color: #856404;">Breach Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; width: 30%;">Breach Type:</td>
                            <td style="padding: 8px 0;">{breach_details.get('type', 'Unknown')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Detection Time:</td>
                            <td style="padding: 8px 0;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Severity Level:</td>
                            <td style="padding: 8px 0;"><strong style="color: #dc3545;">CRITICAL</strong></td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Attack Vector:</td>
                            <td style="padding: 8px 0;">{breach_details.get('vector', 'Under Investigation')}</td>
                        </tr>
                    </table>
                </div>
                
                <!-- Impact Assessment -->
                <div style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h4 style="margin: 0 0 15px 0; color: #721c24;">Impact Assessment</h4>
                    <p style="margin: 0 0 15px 0; color: #721c24;">{breach_details.get('description', 'Breach details are being investigated.')}</p>
                    
                    {f'''
                    <div style="margin-top: 15px;">
                        <strong>Affected Users:</strong> {len(affected_users) if affected_users else 'Unknown'}<br>
                        <strong>Data Types:</strong> {breach_details.get('data_types', 'Under Investigation')}<br>
                        <strong>Estimated Scope:</strong> {breach_details.get('scope', 'Being Assessed')}
                    </div>
                    ''' if affected_users or breach_details.get('data_types') else ''}
                </div>
                
                <!-- Immediate Actions -->
                <div style="background: #d1ecf1; border: 1px solid #bee5eb; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h4 style="margin: 0 0 15px 0; color: #0c5460;">Immediate Actions Required</h4>
                    <ol style="margin: 0; padding-left: 20px; color: #0c5460;">
                        <li>Review security logs immediately</li>
                        <li>Assess the full scope of the breach</li>
                        <li>Implement containment measures</li>
                        <li>Notify affected users if necessary</li>
                        <li>Document all findings and actions taken</li>
                        <li>Consider involving law enforcement if required</li>
                    </ol>
                </div>
                
                <!-- Emergency Contacts -->
                <div style="background: #e2e3e5; border: 1px solid #d6d8db; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h4 style="margin: 0 0 15px 0; color: #383d41;">Emergency Contact Information</h4>
                    <p style="margin: 0; color: #383d41;">
                        <strong>Security Team:</strong> security@chamalink.com<br>
                        <strong>Emergency Hotline:</strong> +254-700-000-000<br>
                        <strong>CEO:</strong> ceo@chamalink.com
                    </p>
                </div>
                
                <!-- Critical Action Button -->
                <div style="text-align: center; padding: 20px; background: #721c24; border-radius: 8px;">
                    <h4 style="margin: 0 0 15px 0; color: white;">IMMEDIATE ACTION REQUIRED</h4>
                    <a href="https://chamalink.com/security-dashboard" 
                       style="background: #fff; color: #721c24; padding: 15px 40px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">
                        ACCESS SECURITY DASHBOARD NOW
                    </a>
                </div>
                
            </div>
            
            <!-- Footer -->
            <div style="text-align: center; padding: 20px; color: #721c24; font-size: 14px;">
                <p style="margin: 0; font-weight: bold;">CRITICAL SECURITY ALERT - DO NOT IGNORE</p>
                <p style="margin: 5px 0 0 0;">ChamaLink Security Monitoring System</p>
            </div>
            
        </body>
        </html>
        """
        
        return html
    
    def _create_suspicious_activity_template(self, activity_details):
        """Create template for suspicious activity alerts"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Suspicious Activity Alert - ChamaLink</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #fd7e14 0%, #ffc107 100%); padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 24px;">⚠️ Suspicious Activity Alert</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">Monitoring Pattern Detected</p>
            </div>
            
            <!-- Activity Details -->
            <div style="background: #fff; border: 1px solid #dee2e6; padding: 30px; border-radius: 0 0 10px 10px;">
                
                <!-- Pattern Info -->
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="margin: 0 0 15px 0; color: #856404;">Activity Pattern</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; width: 30%;">Pattern Type:</td>
                            <td style="padding: 8px 0;">{activity_details.get('pattern', 'Unknown')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Frequency:</td>
                            <td style="padding: 8px 0;">{activity_details.get('frequency', 'N/A')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Time Window:</td>
                            <td style="padding: 8px 0;">{activity_details.get('time_window', 'N/A')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Risk Level:</td>
                            <td style="padding: 8px 0;"><span style="color: #fd7e14; font-weight: bold;">MEDIUM</span></td>
                        </tr>
                    </table>
                </div>
                
                <!-- Details -->
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h4 style="margin: 0 0 15px 0; color: #495057;">Detection Details</h4>
                    <p style="margin: 0; color: #495057;">{activity_details.get('description', 'Suspicious activity pattern detected.')}</p>
                </div>
                
                <!-- Recommended Actions -->
                <div style="background: #d1ecf1; border: 1px solid #bee5eb; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h4 style="margin: 0 0 15px 0; color: #0c5460;">Recommended Actions</h4>
                    <ul style="margin: 0; padding-left: 20px; color: #0c5460;">
                        <li>Review recent activity logs</li>
                        <li>Monitor for escalation</li>
                        <li>Consider rate limiting if necessary</li>
                        <li>Document findings</li>
                    </ul>
                </div>
                
                <!-- Action Button -->
                <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                    <a href="https://chamalink.com/security-dashboard" 
                       style="background: #fd7e14; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Review Activity
                    </a>
                </div>
                
            </div>
            
            <!-- Footer -->
            <div style="text-align: center; padding: 20px; color: #6c757d; font-size: 14px;">
                <p style="margin: 0;">ChamaLink Security Monitoring - Automated Alert</p>
            </div>
            
        </body>
        </html>
        """
        
        return html

# Global instance
security_notifier = SecurityEmailNotifier()
