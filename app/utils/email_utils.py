from flask import current_app, render_template
from flask_mail import Message
from app import mail
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_chama_email(to_email, subject, template, **kwargs):
    """Send email with chama branding"""
    try:
        # Render the email template
        html_content = render_template(template, **kwargs)
        
        # Create message
        msg = Message(
            subject=subject,
            recipients=[to_email],
            html=html_content,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER')
        )
        
        # Set sender name to chama name if provided
        if 'chama' in kwargs:
            chama = kwargs['chama']
            msg.sender = f"{chama.name} <{current_app.config.get('MAIL_DEFAULT_SENDER')}>"
        
        # Send email
        mail.send(msg)
        return True, "Email sent successfully"
        
    except Exception as e:
        current_app.logger.error(f"Error sending email to {to_email}: {str(e)}")
        return False, str(e)

def send_system_email(to_email, subject, template, **kwargs):
    """Send system email with ChamaLink branding"""
    try:
        # Render the email template
        html_content = render_template(template, **kwargs)
        
        # Create message
        msg = Message(
            subject=subject,
            recipients=[to_email],
            html=html_content,
            sender=f"ChamaLink <{current_app.config.get('MAIL_DEFAULT_SENDER')}>"
        )
        
        # Send email
        mail.send(msg)
        return True, "Email sent successfully"
        
    except Exception as e:
        current_app.logger.error(f"Error sending system email to {to_email}: {str(e)}")
        return False, str(e)

def send_bulk_chama_emails(recipients, subject, template, chama, **kwargs):
    """Send bulk emails to chama members"""
    sent_count = 0
    failed_count = 0
    
    for recipient in recipients:
        try:
            success, message = send_chama_email(
                to_email=recipient.email,
                subject=subject,
                template=template,
                chama=chama,
                member=recipient,
                **kwargs
            )
            if success:
                sent_count += 1
            else:
                failed_count += 1
                current_app.logger.error(f"Failed to send email to {recipient.email}: {message}")
        except Exception as e:
            failed_count += 1
            current_app.logger.error(f"Error sending bulk email to {recipient.email}: {str(e)}")
    
    return sent_count, failed_count

def send_notification_email(user, notification):
    """Send email notification to user"""
    try:
        if notification.chama_id:
            # Chama-related notification
            return send_chama_email(
                to_email=user.email,
                subject=notification.title,
                template='emails/notification.html',
                user=user,
                notification=notification,
                chama=notification.chama
            )
        else:
            # System notification
            return send_system_email(
                to_email=user.email,
                subject=notification.title,
                template='emails/system_notification.html',
                user=user,
                notification=notification
            )
    except Exception as e:
        current_app.logger.error(f"Error sending notification email: {str(e)}")
        return False, str(e)
