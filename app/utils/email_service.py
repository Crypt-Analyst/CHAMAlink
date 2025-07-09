import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from flask import current_app, render_template_string
from datetime import datetime

class EmailService:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.port = 587
        self.sender_email = "bilfordbwire@gmail.com"
        self.password = os.getenv('EMAIL_PASSWORD')  # App password for Gmail
        
    def send_email(self, recipient_email, subject, html_content, text_content=None):
        """Send email with HTML content"""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = recipient_email
            
            # Create text part if provided
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            # Create HTML part
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Create secure connection and send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.password)
                server.sendmail(self.sender_email, recipient_email, message.as_string())
            
            return True
        except Exception as e:
            current_app.logger.error(f"Email sending failed: {e}")
            return False
    
    def send_email_verification(self, user, verification_token):
        """Send email verification link"""
        verification_url = f"{os.getenv('BASE_URL', 'http://localhost:5000')}/auth/verify-email/{verification_token}"
        
        subject = "Verify Your ChamaLink Account"
        html_content = self._get_email_template('verification', {
            'user_name': user.full_name,
            'verification_url': verification_url
        })
        
        text_content = f"""
        Hello {user.full_name},
        
        Welcome to ChamaLink! To activate your account, please verify your email address using the link below:
        
        Verify Email Address: {verification_url}
        
        If the link doesn't work, copy and paste it into your browser.
        
        This verification link will expire in 24 hours.
        
        Thank you,
        ChamaLink Team
        """
        
        return self.send_email(
            recipient_email=user.email,
            subject="Verify your ChamaLink account",
            html_content=html_content,
            text_content=text_content
        )
    
    def send_2fa_code_email(self, user, code):
        """Send 2FA verification code via email"""
        try:
            from flask import render_template
            
            html_content = render_template('email/2fa_code.html', user=user, code=code)
            
            text_content = f"""
            Hello {user.first_name or user.username},
            
            You are attempting to log in to your ChamaLink account. Please use the verification code below to complete the login process.
            
            Your Verification Code: {code}
            
            This code will expire in 10 minutes.
            
            Security Notice: If you did not request this code, please ignore this email and contact support immediately.
            
            Best regards,
            ChamaLink Team
            """
            
            return self.send_email(
                recipient_email=user.email,
                subject="ChamaLink - Two-Factor Authentication Code",
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            current_app.logger.error(f"2FA email sending failed: {e}")
            return False
    
    def send_subscription_expiry_warning(self, user, days_remaining):
        """Send subscription expiry warning"""
        subject = f"ChamaLink Subscription Expires in {days_remaining} Days"
        html_content = self._get_email_template('subscription_warning', {
            'user_name': user.full_name,
            'days_remaining': days_remaining,
            'plan_name': user.current_subscription.plan.name.title(),
            'renewal_url': f"{os.getenv('BASE_URL', 'http://localhost:5000')}/subscription/renew"
        })
        
        return self.send_email(user.email, subject, html_content)
    
    def send_subscription_expired(self, user):
        """Send subscription expired notification"""
        subject = "ChamaLink Subscription Expired"
        html_content = self._get_email_template('subscription_expired', {
            'user_name': user.full_name,
            'renewal_url': f"{os.getenv('BASE_URL', 'http://localhost:5000')}/subscription/renew"
        })
        
        return self.send_email(user.email, subject, html_content)
    
    def send_subscription_payment_confirmation(self, user, subscription, payment):
        """Send payment confirmation and subscription details"""
        subject = "ChamaLink Subscription Payment Confirmed"
        html_content = self._get_email_template('payment_confirmation', {
            'user_name': user.full_name,
            'plan_name': subscription.plan.name.title(),
            'amount': f"KES {payment.amount:,.0f}",
            'start_date': subscription.start_date.strftime('%B %d, %Y'),
            'end_date': subscription.end_date.strftime('%B %d, %Y at %I:%M %p'),
            'receipt_number': payment.mpesa_receipt_number
        })
        
        return self.send_email(user.email, subject, html_content)
    
    def send_loan_approval_request(self, admin, loan_application, approval_token):
        """Send loan approval request to admin"""
        approval_url = f"{os.getenv('BASE_URL', 'http://localhost:5000')}/loans/approve-token/{approval_token.token}"
        
        subject = f"Loan Approval Required - {loan_application.user.full_name}"
        html_content = self._get_email_template('loan_approval', {
            'admin_name': admin.full_name,
            'applicant_name': loan_application.user.full_name,
            'amount': loan_application.formatted_amount,
            'purpose': loan_application.purpose,
            'chama_name': loan_application.chama.name,
            'approval_url': approval_url,
            'expires_at': approval_token.expires_at.strftime('%B %d, %Y at %I:%M %p')
        })
        
        return self.send_email(admin.email, subject, html_content)
    
    def send_account_locked_notification(self, user):
        """Send account locked notification"""
        subject = "ChamaLink Account Temporarily Locked"
        html_content = self._get_email_template('account_locked', {
            'user_name': user.full_name,
            'unlock_time': user.locked_until.strftime('%B %d, %Y at %I:%M %p') if user.locked_until else "24 hours"
        })
        
        return self.send_email(user.email, subject, html_content)
    
    def _get_email_template(self, template_name, context):
        """Get email template with context variables"""
        templates = {
            'verification': """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    .email-container { max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }
                    .header { background: #667eea; color: white; padding: 20px; text-align: center; }
                    .content { padding: 30px 20px; }
                    .button { display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
                    .footer { background: #f8f9fa; padding: 20px; text-align: center; color: #6c757d; }
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <h1>ChamaLink</h1>
                        <p>Welcome to Kenya's Premier Chama Management Platform</p>
                    </div>
                    <div class="content">
                        <h2>Welcome, {{ user_name }}!</h2>
                        <p>Thank you for joining ChamaLink. To complete your registration and secure your account, please verify your email address.</p>
                        <p>Click the button below to verify your email:</p>
                        <a href="{{ verification_url }}" class="button">Verify Email Address</a>
                        <p>If the button doesn't work, copy and paste this link into your browser:</p>
                        <p>{{ verification_url }}</p>
                        <p>This verification link will expire in 24 hours for security reasons.</p>
                    </div>
                    <div class="footer">
                        <p>&copy; 2025 ChamaLink. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            
            'subscription_warning': """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    .email-container { max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }
                    .header { background: #ffc107; color: #212529; padding: 20px; text-align: center; }
                    .content { padding: 30px 20px; }
                    .button { display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
                    .warning { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <h1>⚠️ Subscription Expiry Notice</h1>
                    </div>
                    <div class="content">
                        <h2>Hello {{ user_name }},</h2>
                        <div class="warning">
                            <strong>Your ChamaLink {{ plan_name }} subscription will expire in {{ days_remaining }} days.</strong>
                        </div>
                        <p>To continue enjoying uninterrupted access to your chama management features, please renew your subscription.</p>
                        <a href="{{ renewal_url }}" class="button">Renew Subscription</a>
                        <p>Don't lose access to your important chama data and features!</p>
                    </div>
                    <div class="footer">
                        <p>&copy; 2025 ChamaLink. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            
            'subscription_expired': """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    .email-container { max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }
                    .header { background: #dc3545; color: white; padding: 20px; text-align: center; }
                    .content { padding: 30px 20px; }
                    .button { display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
                    .expired { background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; margin: 20px 0; }
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <h1>🚫 Subscription Expired</h1>
                    </div>
                    <div class="content">
                        <h2>Hello {{ user_name }},</h2>
                        <div class="expired">
                            <strong>Your ChamaLink subscription has expired.</strong>
                        </div>
                        <p>Your account access has been limited. To restore full functionality and access to your chama data, please renew your subscription immediately.</p>
                        <a href="{{ renewal_url }}" class="button">Renew Now</a>
                        <p>Your data is safe and will be restored once you renew your subscription.</p>
                    </div>
                    <div class="footer">
                        <p>&copy; 2025 ChamaLink. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            
            'payment_confirmation': """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    .email-container { max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }
                    .header { background: #28a745; color: white; padding: 20px; text-align: center; }
                    .content { padding: 30px 20px; }
                    .details { background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 5px; margin: 20px 0; }
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <h1>✅ Payment Confirmed</h1>
                    </div>
                    <div class="content">
                        <h2>Hello {{ user_name }},</h2>
                        <p>Your ChamaLink subscription payment has been successfully processed!</p>
                        <div class="details">
                            <h3>Subscription Details:</h3>
                            <p><strong>Plan:</strong> {{ plan_name }}</p>
                            <p><strong>Amount Paid:</strong> {{ amount }}</p>
                            <p><strong>Start Date:</strong> {{ start_date }}</p>
                            <p><strong>Expires On:</strong> {{ end_date }}</p>
                            <p><strong>Receipt Number:</strong> {{ receipt_number }}</p>
                        </div>
                        <p>Thank you for choosing ChamaLink for your chama management needs!</p>
                    </div>
                    <div class="footer">
                        <p>&copy; 2025 ChamaLink. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            
            'loan_approval': """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    .email-container { max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }
                    .header { background: #007bff; color: white; padding: 20px; text-align: center; }
                    .content { padding: 30px 20px; }
                    .button { display: inline-block; background: #28a745; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
                    .loan-details { background: #e7f3ff; border: 1px solid #b3d9ff; padding: 15px; border-radius: 5px; margin: 20px 0; }
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <h1>🏛️ Loan Approval Required</h1>
                    </div>
                    <div class="content">
                        <h2>Hello {{ admin_name }},</h2>
                        <p>A new loan application requires your approval in ChamaLink.</p>
                        <div class="loan-details">
                            <h3>Loan Application Details:</h3>
                            <p><strong>Applicant:</strong> {{ applicant_name }}</p>
                            <p><strong>Amount:</strong> {{ amount }}</p>
                            <p><strong>Purpose:</strong> {{ purpose }}</p>
                            <p><strong>Chama:</strong> {{ chama_name }}</p>
                        </div>
                        <p>Click the secure link below to review and approve/reject this loan:</p>
                        <a href="{{ approval_url }}" class="button">Review Loan Application</a>
                        <p><strong>Important:</strong> This approval link expires on {{ expires_at }}.</p>
                        <p>Please provide your name and password to complete the approval process.</p>
                    </div>
                    <div class="footer">
                        <p>&copy; 2025 ChamaLink. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            
            'account_locked': """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    .email-container { max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }
                    .header { background: #dc3545; color: white; padding: 20px; text-align: center; }
                    .content { padding: 30px 20px; }
                    .security { background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; margin: 20px 0; }
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <h1>🔒 Account Security Alert</h1>
                    </div>
                    <div class="content">
                        <h2>Hello {{ user_name }},</h2>
                        <div class="security">
                            <strong>Your ChamaLink account has been temporarily locked due to multiple failed login attempts.</strong>
                        </div>
                        <p>For security reasons, your account will be automatically unlocked at {{ unlock_time }}.</p>
                        <p>If you didn't attempt to log in, please contact our support team immediately.</p>
                        <p>To protect your account in the future:</p>
                        <ul>
                            <li>Use a strong, unique password</li>
                            <li>Never share your login credentials</li>
                            <li>Enable email verification for added security</li>
                        </ul>
                    </div>
                    <div class="footer">
                        <p>&copy; 2025 ChamaLink. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        }
        
        template = templates.get(template_name, "")
        for key, value in context.items():
            template = template.replace(f"{{{{ {key} }}}}", str(value))
        
        return template

# Initialize email service
email_service = EmailService()

# Export the send_email function for easy importing
def send_email(recipient_email, subject, html_content, text_content=None):
    """Convenience function to send email using the email service"""
    return email_service.send_email(recipient_email, subject, html_content, text_content)

# Export other email functions
def send_subscription_email(recipient_email, subject, html_content, text_content=None):
    """Convenience function for subscription emails"""
    return email_service.send_email(recipient_email, subject, html_content, text_content)

def send_email_verification(user, verification_token):
    """Send email verification link"""
    return email_service.send_email_verification(user, verification_token)

def send_subscription_expiry_warning(user, days_remaining):
    """Send subscription expiry warning"""
    return email_service.send_subscription_expiry_warning(user, days_remaining)

def send_subscription_expired(user):
    """Send subscription expired notification"""
    return email_service.send_subscription_expired(user)

def send_subscription_payment_confirmation(user, subscription, payment):
    """Send subscription payment confirmation"""
    return email_service.send_subscription_payment_confirmation(user, subscription, payment)

def send_loan_approval_request(admin, loan_application, approval_token):
    """Send loan approval request to admin"""
    return email_service.send_loan_approval_request(admin, loan_application, approval_token)

def send_account_locked_notification(user):
    """Send account locked notification"""
    return email_service.send_account_locked_notification(user)

def send_2fa_code_email(user, code):
    """Send 2FA verification code via email"""
    return email_service.send_2fa_code_email(user, code)

def send_2fa_code_email(user_email, code):
    """Send 2FA verification code via email"""
    try:
        from app.models import User
        user = User.query.filter_by(email=user_email).first()
        
        if not user:
            return False
            
        email_service = EmailService()
        return email_service.send_2fa_code_email(user, code)
        
    except Exception as e:
        current_app.logger.error(f"2FA email helper failed: {e}")
        return False
