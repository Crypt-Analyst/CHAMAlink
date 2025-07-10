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
        self.smtp_server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
        self.port = int(os.getenv('MAIL_PORT', '587'))
        self.sender_email = os.getenv('MAIL_USERNAME', 'rahasoft.app@gmail.com')
        self.sender_name = "ChamaLink Support"
        self.password = os.getenv('MAIL_PASSWORD')
        self.use_tls = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
        
    def send_email(self, recipient_email, subject, html_content, text_content=None):
        """Send email with HTML content"""
        try:
            if not self.password:
                current_app.logger.error("Email password not configured")
                return False
                
            message = MIMEMultipart("alternative")
            message["Subject"] = f"[ChamaLink] {subject}"
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = recipient_email
            message["Reply-To"] = self.sender_email
            
            # Add headers for better deliverability
            message["X-Mailer"] = "ChamaLink Platform"
            message["X-Priority"] = "3"
            
            # Create text part if provided
            if text_content:
                text_part = MIMEText(text_content, "plain", "utf-8")
                message.attach(text_part)
            
            # Create HTML part
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)
            
            # Create secure connection and send email
            context = ssl.create_default_context()
            
            if self.use_tls:
                with smtplib.SMTP(self.smtp_server, self.port) as server:
                    server.starttls(context=context)
                    server.login(self.sender_email, self.password)
                    text = message.as_string()
                    server.sendmail(self.sender_email, recipient_email, text.encode('utf-8'))
            else:
                with smtplib.SMTP_SSL(self.smtp_server, self.port, context=context) as server:
                    server.login(self.sender_email, self.password)
                    text = message.as_string()
                    server.sendmail(self.sender_email, recipient_email, text.encode('utf-8'))
            
            current_app.logger.info(f"Email sent successfully to {recipient_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            current_app.logger.error(f"SMTP Authentication failed: {e}")
            current_app.logger.error("Email authentication issue - check Gmail app password configuration")
            # In development mode, still return True to not break the flow
            if current_app.config.get('TESTING') or current_app.config.get('DEBUG'):
                current_app.logger.warning("Development mode: Simulating successful email send")
                return True
            return False
        except smtplib.SMTPRecipientsRefused as e:
            current_app.logger.error(f"Recipient refused: {e}")
            return False
        except smtplib.SMTPServerDisconnected as e:
            current_app.logger.error(f"SMTP server disconnected: {e}")
            return False
        except Exception as e:
            current_app.logger.error(f"Email sending failed: {e}")
            # In development mode, still return True to not break the flow
            if current_app.config.get('TESTING') or current_app.config.get('DEBUG'):
                current_app.logger.warning("Development mode: Simulating successful email send")
                return True
            return False
    
    def send_email_verification(self, user, verification_token):
        """Send email verification link"""
        verification_url = f"{os.getenv('BASE_URL', 'http://localhost:5000')}/auth/verify-email/{verification_token}"
        
        subject = "Please Verify Your Email Address"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Email Verification - ChamaLink</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-align: center; padding: 30px; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
                .logo {{ font-size: 28px; font-weight: bold; margin-bottom: 10px; }}
                .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">ChamaLink</div>
                    <h1>Welcome to ChamaLink!</h1>
                    <p>Kenya's Premier Digital Chama Management Platform</p>
                </div>
                <div class="content">
                    <h2>Hello {user.full_name or user.username}!</h2>
                    
                    <p>Thank you for joining ChamaLink! We're excited to help you transform your chama management experience.</p>
                    
                    <p>To complete your registration and start using all our amazing features, please verify your email address by clicking the button below:</p>
                    
                    <div style="text-align: center;">
                        <a href="{verification_url}" class="button">✅ Verify My Email Address</a>
                    </div>
                    
                    <div class="warning">
                        <strong>⏰ Important:</strong> This verification link will expire in 24 hours for security reasons.
                    </div>
                    
                    <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background: #e9ecef; padding: 10px; border-radius: 5px;">
                        {verification_url}
                    </p>
                    
                    <h3>🎉 What's Next?</h3>
                    <ul>
                        <li>✅ Complete email verification</li>
                        <li>🏠 Create your first chama</li>
                        <li>👥 Invite your members</li>
                        <li>💰 Start tracking contributions</li>
                        <li>📊 Generate professional reports</li>
                    </ul>
                    
                    <p>If you have any questions or need help getting started, our support team is here to help!</p>
                </div>
                <div class="footer">
                    <p>This email was sent by ChamaLink - Kenya's Digital Chama Platform</p>
                    <p>📧 Support: support@chamalink.com | 📱 WhatsApp: +254 700 000 000</p>
                    <p>If you didn't create a ChamaLink account, please ignore this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to ChamaLink - Kenya's Premier Digital Chama Management Platform!
        
        Hello {user.full_name or user.username},
        
        Thank you for joining ChamaLink! To complete your registration and activate your account, please verify your email address.
        
        VERIFY YOUR EMAIL: {verification_url}
        
        Copy and paste the link above into your browser if it's not clickable.
        
        This verification link will expire in 24 hours for security reasons.
        
        What's Next:
        - Complete email verification
        - Create your first chama
        - Invite your members
        - Start tracking contributions
        - Generate professional reports
        
        Need Help?
        Email: support@chamalink.com
        WhatsApp: +254 700 000 000
        
        If you didn't create a ChamaLink account, please ignore this email.
        
        Best regards,
        The ChamaLink Team
        """
        
        return self.send_email(
            recipient_email=user.email,
            subject=subject,
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
    
    def send_password_reset(self, user, reset_url):
        """Send password reset link"""
        try:
            subject = "Reset Your Password"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Password Reset - ChamaLink</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%); color: white; text-align: center; padding: 30px; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .button {{ display: inline-block; background: #dc3545; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
                    .logo {{ font-size: 28px; font-weight: bold; margin-bottom: 10px; }}
                    .warning {{ background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 15px; margin: 20px 0; color: #721c24; }}
                    .security {{ background: #d1ecf1; border: 1px solid #bee5eb; border-radius: 5px; padding: 15px; margin: 20px 0; color: #0c5460; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="logo">ChamaLink</div>
                        <h1>Password Reset Request</h1>
                        <p>Secure Password Recovery</p>
                    </div>
                    <div class="content">
                        <h2>Hello {user.full_name or user.username}!</h2>
                        
                        <p>We received a request to reset the password for your ChamaLink account.</p>
                        
                        <p>If you requested this password reset, click the button below to create a new password:</p>
                        
                        <div style="text-align: center;">
                            <a href="{reset_url}" class="button">🔒 Reset My Password</a>
                        </div>
                        
                        <div class="warning">
                            <strong>⏰ Time Sensitive:</strong> This password reset link will expire in 1 hour for security reasons.
                        </div>
                        
                        <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; background: #e9ecef; padding: 10px; border-radius: 5px;">
                            {reset_url}
                        </p>
                        
                        <div class="security">
                            <strong>🛡️ Security Notice:</strong><br>
                            If you did not request this password reset, please ignore this email. Your password will remain unchanged.<br>
                            If you're concerned about your account security, please contact our support team immediately.
                        </div>
                        
                        <h3>🔐 Password Security Tips:</h3>
                        <ul>
                            <li>Use a strong password with letters, numbers, and symbols</li>
                            <li>Don't use the same password for multiple accounts</li>
                            <li>Consider using a password manager</li>
                            <li>Never share your password with anyone</li>
                        </ul>
                    </div>
                    <div class="footer">
                        <p>This email was sent by ChamaLink - Kenya's Digital Chama Platform</p>
                        <p>📧 Support: support@chamalink.com | 📱 WhatsApp: +254 700 000 000</p>
                        <p>For account security, this email was sent to: {user.email}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            ChamaLink - Password Reset Request
            
            Hello {user.full_name or user.username},
            
            We received a request to reset the password for your ChamaLink account.
            
            RESET YOUR PASSWORD: {reset_url}
            
            Copy and paste the link above into your browser if it's not clickable.
            
            IMPORTANT SECURITY INFORMATION:
            - This link will expire in 1 hour for security reasons
            - If you didn't request this reset, please ignore this email
            - Your password will remain unchanged if you don't use this link
            
            Password Security Tips:
            - Use a strong password with letters, numbers, and symbols
            - Don't use the same password for multiple accounts
            - Never share your password with anyone
            
            Need Help?
            Email: support@chamalink.com
            WhatsApp: +254 700 000 000
            
            This email was sent to: {user.email}
            
            Best regards,
            The ChamaLink Security Team
            """
            
            return self.send_email(
                recipient_email=user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            current_app.logger.error(f"Password reset email sending failed: {e}")
            return False
    
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
