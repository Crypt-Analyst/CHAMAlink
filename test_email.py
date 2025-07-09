#!/usr/bin/env python3
"""
Email configuration test script for ChamaLink
This script helps you test email functionality and provides setup instructions.
"""
import os
import sys
sys.path.insert(0, os.path.abspath('.'))

from app import create_app
from app.utils.email_service import send_email

def test_email_configuration():
    """Test email configuration and provide setup instructions"""
    print("🔧 Email Configuration Test")
    print("=" * 50)
    
    # Check if email password is set
    email_password = os.getenv('EMAIL_PASSWORD')
    if not email_password or email_password == 'your_gmail_app_password_here':
        print("❌ Email password not configured!")
        print("\n📋 Gmail App Password Setup Instructions:")
        print("1. Go to Gmail settings: https://myaccount.google.com/security")
        print("2. Enable 2-Step Verification (if not already enabled)")
        print("3. Go to 'App passwords' section")
        print("4. Generate a new app password for 'Mail'")
        print("5. Copy the 16-character app password")
        print("6. Update your .env file:")
        print("   EMAIL_PASSWORD=your_16_character_app_password")
        print("\n⚠️  NOTE: Use the app password, NOT your regular Gmail password!")
        return False
    
    # Test email sending
    app = create_app()
    with app.app_context():
        print("✅ Email password configured")
        print("🔄 Testing email sending...")
        
        # Test with a simple email
        try:
            result = send_email(
                'test@example.com',
                'ChamaLink Test Email',
                '''
                <html>
                <body>
                    <h2>ChamaLink Email Test</h2>
                    <p>This is a test email from ChamaLink.</p>
                    <p>If you receive this, email configuration is working!</p>
                </body>
                </html>
                ''',
                'ChamaLink Email Test - This is a test email from ChamaLink.'
            )
            
            if result:
                print("✅ Email sending test successful!")
                print("📧 You should receive a test email shortly at test@example.com")
                return True
            else:
                print("❌ Email sending failed!")
                print("💡 Check your app password and internet connection")
                return False
                
        except Exception as e:
            print(f"❌ Email sending error: {e}")
            print("💡 Common issues:")
            print("   - Invalid app password")
            print("   - 2-Step Verification not enabled")
            print("   - Internet connection issues")
            return False

def send_test_verification_email():
    """Send a test verification email"""
    app = create_app()
    with app.app_context():
        from app.models.user import User
        
        # Find a user to send test email to
        user = User.query.first()
        if not user:
            print("❌ No users found in database")
            return False
        
        print(f"📧 Sending test verification email to {user.email}")
        
        try:
            from app.utils.email_service import send_email_verification
            import secrets
            
            # Generate a test token
            test_token = secrets.token_urlsafe(32)
            
            result = send_email_verification(user, test_token)
            
            if result:
                print("✅ Test verification email sent successfully!")
                print(f"📧 Check {user.email} for the verification email")
                return True
            else:
                print("❌ Failed to send verification email")
                return False
                
        except Exception as e:
            print(f"❌ Error sending verification email: {e}")
            return False

if __name__ == '__main__':
    print("🚀 ChamaLink Email Configuration Test")
    print("=" * 50)
    
    # Test basic email configuration
    if test_email_configuration():
        print("\n" + "=" * 50)
        print("🎯 Testing user verification email...")
        send_test_verification_email()
        
        print("\n" + "=" * 50)
        print("✅ Email system is working!")
        print("💡 Next steps:")
        print("   1. Replace 'test@example.com' with your actual email")
        print("   2. Test user registration with email verification")
        print("   3. Set up production email service for deployment")
    else:
        print("\n❌ Email configuration needs to be fixed first")
        print("Please follow the setup instructions above")
