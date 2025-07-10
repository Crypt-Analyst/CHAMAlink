#!/usr/bin/env python3
"""
Direct email test with new credentials
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_email_direct():
    """Test email sending directly with the new credentials"""
    print("🔧 DIRECT EMAIL TEST")
    print("=" * 30)
    
    # Email configuration
    smtp_server = "smtp.gmail.com"
    port = 587
    sender_email = "rahasoft.app@gmail.com"
    password = "lcxlgwxwpktzmtgw"
    
    # Test email
    recipient = "test@example.com"  # Replace with a real email for testing
    subject = "ChamaLink Test Email"
    
    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"ChamaLink Support <{sender_email}>"
    message["To"] = recipient
    
    # Create the HTML content
    html = """
    <html>
      <body>
        <h2>🎉 ChamaLink Email Test</h2>
        <p>This is a test email to verify that the ChamaLink email system is working correctly.</p>
        <p>If you receive this email, the configuration is successful!</p>
        <hr>
        <p><small>This is an automated test message from ChamaLink.</small></p>
      </body>
    </html>
    """
    
    text = """
    ChamaLink Email Test
    
    This is a test email to verify that the ChamaLink email system is working correctly.
    If you receive this email, the configuration is successful!
    
    This is an automated test message from ChamaLink.
    """
    
    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    
    # Add HTML/plain-text parts to MIMEMultipart message
    message.attach(part1)
    message.attach(part2)
    
    # Try to send the email
    try:
        print(f"📧 Attempting to send email via {smtp_server}:{port}")
        print(f"📤 From: {sender_email}")
        print(f"📥 To: {recipient}")
        
        # Create secure connection and send email
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls(context=context)
            print("🔒 TLS connection established")
            
            server.login(sender_email, password)
            print("✅ SMTP authentication successful")
            
            server.sendmail(sender_email, recipient, message.as_string())
            print("✅ Email sent successfully!")
            
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication failed: {e}")
        print("💡 Please check:")
        print("   1. Gmail account has 2FA enabled")
        print("   2. App password is correctly generated")
        print("   3. App password is exactly 16 characters")
        return False
        
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False

if __name__ == '__main__':
    success = test_email_direct()
    if success:
        print("\n🎉 Email configuration is working!")
    else:
        print("\n❌ Email configuration needs attention.")
