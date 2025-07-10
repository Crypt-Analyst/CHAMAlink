#!/usr/bin/env python3
"""
Flask Email Test - Test email sending from within Flask application context
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up Flask app
os.environ['FLASK_ENV'] = 'testing'

from app import create_app
from app.utils.email_service import EmailService

def test_flask_email():
    """Test email sending from within Flask app context"""
    print("🧪 Testing email functionality within Flask app context...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Initialize email service
            email_service = EmailService()
            print("✅ Email service initialized successfully")
            
            # Test basic email sending
            print("\n📧 Testing basic email sending...")
            result = email_service.send_email(
                recipient_email="test@example.com",
                subject="ChamaLink Test Email - Flask Context",
                text_content="This is a test email sent from Flask app context.",
                html_content="<h2>ChamaLink Test Email</h2><p>This is a test email sent from Flask app context.</p>"
            )
            
            if result:
                print("✅ Basic email sending works")
            else:
                print("❌ Basic email sending failed")
                return False
            
            # Test verification email template
            print("\n📨 Testing verification email template...")
            verification_result = email_service.send_email_verification(
                user=type('obj', (object,), {
                    'email': 'test@example.com', 
                    'username': 'Test User',
                    'full_name': 'Test User Full Name'
                })(),
                verification_token="test_token_123"
            )
            
            if verification_result:
                print("✅ Verification email template works")
            else:
                print("❌ Verification email template failed")
                return False
            
            # Test password reset email template  
            print("\n🔑 Testing password reset email template...")
            reset_result = email_service.send_password_reset(
                user=type('obj', (object,), {
                    'email': 'test@example.com', 
                    'username': 'Test User',
                    'full_name': 'Test User Full Name'
                })(),
                reset_url="http://localhost:5000/auth/reset_password/reset_token_123"
            )
            
            if reset_result:
                print("✅ Password reset email template works")
            else:
                print("❌ Password reset email template failed")
                return False
                
            print("\n🎉 All Flask email tests passed!")
            return True
            
        except Exception as e:
            print(f"❌ Flask email test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def test_real_email_delivery():
    """Test actual email delivery to a real address"""
    print("\n📮 Testing real email delivery...")
    
    app = create_app()
    
    with app.app_context():
        try:
            email_service = EmailService()
            
            # Send to a real email address (replace with your test email)
            test_email = "rahasoft.app@gmail.com"  # Using same account for testing
            
            result = email_service.send_email(
                recipient_email=test_email,
                subject="ChamaLink Production Test - Real Email",
                text_content="This is a real email delivery test from ChamaLink production system.",
                html_content="""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #2563eb;">ChamaLink Production Test</h2>
                    <p>This is a real email delivery test from the ChamaLink production system.</p>
                    <p>If you receive this email, the email system is working correctly.</p>
                    <hr>
                    <p style="color: #666; font-size: 12px;">Sent from ChamaLink Platform</p>
                </div>
                """
            )
            
            if result:
                print(f"✅ Real email sent successfully to {test_email}")
                print("Check your inbox to confirm delivery")
                return True
            else:
                print(f"❌ Failed to send real email to {test_email}")
                return False
                
        except Exception as e:
            print(f"❌ Real email delivery test failed: {str(e)}")
            return False

if __name__ == "__main__":
    print("🚀 Starting Flask Email Tests...")
    
    # Test 1: Flask context email functionality
    flask_test_passed = test_flask_email()
    
    # Test 2: Real email delivery
    real_email_passed = test_real_email_delivery()
    
    print("\n" + "="*60)
    print("📊 FLASK EMAIL TEST RESULTS:")
    print("="*60)
    print(f"Flask Context Email: {'✅ PASS' if flask_test_passed else '❌ FAIL'}")
    print(f"Real Email Delivery: {'✅ PASS' if real_email_passed else '❌ FAIL'}")
    
    if flask_test_passed and real_email_passed:
        print("\n🎉 All email tests passed! Email system is production ready.")
        sys.exit(0)
    else:
        print("\n⚠️ Some email tests failed. Check configuration and credentials.")
        sys.exit(1)
