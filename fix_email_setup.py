#!/usr/bin/env python3
"""
Email Setup Fix Script for ChamaLink
This script helps fix email configuration issues
"""

import os
import sys
sys.path.insert(0, os.path.abspath('.'))

from app import create_app
from app.utils.email_service import EmailService

def fix_email_configuration():
    """Fix and test email configuration"""
    print("🔧 ChamaLink Email Configuration Fix")
    print("=" * 50)
    
    # Check current configuration
    print("Current Email Configuration:")
    print(f"MAIL_SERVER: {os.getenv('MAIL_SERVER', 'Not set')}")
    print(f"MAIL_PORT: {os.getenv('MAIL_PORT', 'Not set')}")
    print(f"MAIL_USERNAME: {os.getenv('MAIL_USERNAME', 'Not set')}")
    print(f"MAIL_PASSWORD: {'*' * len(os.getenv('MAIL_PASSWORD', ''))}")
    print(f"MAIL_USE_TLS: {os.getenv('MAIL_USE_TLS', 'Not set')}")
    
    # Test with app context
    app = create_app()
    with app.app_context():
        try:
            email_service = EmailService()
            
            # Try a simple test email
            test_result = email_service.send_email(
                recipient_email="test@example.com",
                subject="ChamaLink Email Configuration Test",
                html_content="""
                <html>
                <body>
                    <h2>✅ Email Configuration Working!</h2>
                    <p>This test email confirms your ChamaLink email setup is working correctly.</p>
                    <p><strong>Time:</strong> {}</p>
                    <p><strong>From:</strong> ChamaLink System</p>
                </body>
                </html>
                """.format(str(app.config.get('datetime', 'Unknown'))),
                text_content="Email Configuration Test - ChamaLink system is working correctly!"
            )
            
            if test_result:
                print("\n✅ EMAIL CONFIGURATION IS WORKING!")
                print("📧 Test email would be sent successfully")
                print("\n🎯 Next Steps:")
                print("   1. Email verification will work for new users")
                print("   2. Password reset emails will be sent")
                print("   3. System notifications will be delivered")
                return True
            else:
                print("\n❌ EMAIL CONFIGURATION FAILED!")
                provide_troubleshooting_steps()
                return False
                
        except Exception as e:
            print(f"\n❌ EMAIL SERVICE ERROR: {e}")
            provide_troubleshooting_steps()
            return False

def provide_troubleshooting_steps():
    """Provide troubleshooting steps for email issues"""
    print("\n🔧 TROUBLESHOOTING STEPS:")
    print("=" * 30)
    
    print("\n1. Gmail App Password Setup:")
    print("   • Go to: https://myaccount.google.com/security")
    print("   • Enable 2-Step Verification")
    print("   • Go to 'App passwords' section")
    print("   • Generate new app password for 'Mail'")
    print("   • Copy the 16-character password")
    
    print("\n2. Update .env file:")
    print("   MAIL_PASSWORD=your_16_character_app_password")
    print("   (Replace the current password with your new app password)")
    
    print("\n3. Alternative Email Providers:")
    print("   • Outlook: smtp-mail.outlook.com:587")
    print("   • Yahoo: smtp.mail.yahoo.com:587")
    print("   • Custom SMTP: Check with your provider")
    
    print("\n4. Verify Environment Variables:")
    print("   • Restart your application after .env changes")
    print("   • Check for typos in email/password")
    print("   • Ensure no spaces in .env values")

def create_email_verification_test():
    """Create a test for email verification functionality"""
    app = create_app()
    with app.app_context():
        from app.models.user import User
        from app.utils.email_service import send_email_verification
        import secrets
        
        # Find a test user
        user = User.query.first()
        if user:
            print(f"\n📧 Testing email verification for: {user.email}")
            
            # Generate test verification token
            test_token = secrets.token_urlsafe(32)
            
            try:
                result = send_email_verification(user, test_token)
                if result:
                    print("✅ Email verification test successful!")
                    return True
                else:
                    print("❌ Email verification test failed!")
                    return False
            except Exception as e:
                print(f"❌ Email verification error: {e}")
                return False
        else:
            print("❌ No users found for testing")
            return False

if __name__ == '__main__':
    print("🚀 Starting Email Configuration Fix...")
    
    # Test current configuration
    email_working = fix_email_configuration()
    
    if email_working:
        print("\n🎉 EMAIL SYSTEM IS READY!")
        print("Testing email verification...")
        verification_working = create_email_verification_test()
        
        if verification_working:
            print("\n✅ ALL EMAIL FUNCTIONS WORKING!")
        else:
            print("\n⚠️ Email verification needs attention")
    else:
        print("\n🔧 Follow the troubleshooting steps above")
        print("Then run this script again to test")
    
    print("\n" + "=" * 50)
    print("Email fix script completed!")
