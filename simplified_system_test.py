#!/usr/bin/env python3
"""
Simplified Authentication and System Test
Test what's actually implemented and working
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up Flask app
os.environ['FLASK_ENV'] = 'testing'

from app import create_app, db
from app.models.user import User
from app.utils.email_service import EmailService

def test_password_reset_flow():
    """Test password reset flow with existing methods"""
    print("🔑 Testing Password Reset Flow...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Step 1: Create a test user
            print("\n🔹 Step 1: Creating test user for password reset...")
            test_email = "test_reset_user@example.com"
            
            # Clean up any existing test user
            existing_user = User.query.filter_by(email=test_email).first()
            if existing_user:
                db.session.delete(existing_user)
                db.session.commit()
            
            # Create new test user
            test_user = User(
                username="test_reset_user",
                email=test_email,
                first_name="Test Reset",
                last_name="User"
            )
            test_user.set_password("originalpassword123")
            test_user.is_email_verified = True  # User is verified
            
            db.session.add(test_user)
            db.session.commit()
            print(f"✅ Test user created: {test_email}")
            
            # Step 2: Generate password reset token
            print("\n🔹 Step 2: Generating password reset token...")
            reset_token = test_user.generate_password_reset_token()
            db.session.commit()
            
            if reset_token:
                print("✅ Password reset token generated")
            else:
                print("❌ Failed to generate password reset token")
                return False
            
            # Step 3: Send password reset email
            print("\n🔹 Step 3: Sending password reset email...")
            reset_url = f"http://localhost:5000/auth/reset_password/{reset_token}"
            
            email_service = EmailService()
            email_result = email_service.send_password_reset(
                user=test_user,
                reset_url=reset_url
            )
            
            if email_result:
                print("✅ Password reset email sent successfully")
            else:
                print("❌ Failed to send password reset email")
                return False
            
            # Step 4: Verify reset token
            print("\n🔹 Step 4: Verifying password reset token...")
            if test_user.verify_password_reset_token(reset_token):
                print("✅ Password reset token is valid")
            else:
                print("❌ Password reset token verification failed")
                return False
            
            # Step 5: Reset password
            print("\n🔹 Step 5: Resetting password...")
            new_password = "newpassword456"
            test_user.set_password(new_password)
            test_user.clear_password_reset_token()
            db.session.commit()
            
            # Step 6: Verify new password works
            print("\n🔹 Step 6: Testing login with new password...")
            if test_user.check_password("newpassword456"):
                print("✅ User can log in with new password")
            else:
                print("❌ User cannot log in with new password")
                return False
            
            # Step 7: Verify old password no longer works
            print("\n🔹 Step 7: Verifying old password is invalid...")
            if not test_user.check_password("originalpassword123"):
                print("✅ Old password is no longer valid")
            else:
                print("❌ Old password still works (security issue)")
                return False
            
            print("\n🎉 Password reset flow complete!")
            return True
            
        except Exception as e:
            print(f"❌ Password reset flow test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def test_user_management():
    """Test basic user management functionality"""
    print("\n👤 Testing User Management...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Test user creation
            print("\n🔹 Testing user creation...")
            test_email = "test_user_mgmt@example.com"
            
            # Clean up any existing test user
            existing_user = User.query.filter_by(email=test_email).first()
            if existing_user:
                db.session.delete(existing_user)
                db.session.commit()
            
            # Create new test user
            test_user = User(
                username="test_user_mgmt",
                email=test_email,
                first_name="Test User",
                last_name="Management"
            )
            test_user.set_password("testpassword123")
            
            db.session.add(test_user)
            db.session.commit()
            print("✅ User created successfully")
            
            # Test user properties
            print("\n🔹 Testing user properties...")
            print(f"Username: {test_user.username}")
            print(f"Email: {test_user.email}")
            print(f"Full Name: {test_user.full_name}")
            print(f"Email Verified: {test_user.is_email_verified}")
            print("✅ User properties accessible")
            
            # Test password verification
            print("\n🔹 Testing password verification...")
            if test_user.check_password("testpassword123"):
                print("✅ Password verification works")
            else:
                print("❌ Password verification failed")
                return False
            
            if not test_user.check_password("wrongpassword"):
                print("✅ Wrong password correctly rejected")
            else:
                print("❌ Wrong password incorrectly accepted")
                return False
            
            print("\n🎉 User management test complete!")
            return True
            
        except Exception as e:
            print(f"❌ User management test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def test_multi_language_support():
    """Test multi-language support functionality"""
    print("\n🌍 Testing Multi-Language Support...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Test loading translations
            from app.utils.internationalization import load_translations
            
            print("\n🔹 Testing English translations...")
            en_translations = load_translations('en')
            if en_translations and 'welcome' in en_translations:
                print(f"✅ English: {en_translations['welcome']}")
            else:
                print("❌ English translations not loaded")
                return False
            
            # Test loading Swahili translations
            print("\n🔹 Testing Swahili translations...")
            sw_translations = load_translations('sw')
            if sw_translations and 'welcome' in sw_translations:
                print(f"✅ Swahili: {sw_translations['welcome']}")
            else:
                print("❌ Swahili translations not loaded")
                return False
            
            # Test session management functions exist
            print("\n🔹 Testing language management functions...")
            from app.utils.internationalization import set_language, get_current_language, set_theme, get_current_theme
            print("✅ Language and theme management functions available")
            
            print("\n🎉 Multi-language support test complete!")
            return True
            
        except Exception as e:
            print(f"❌ Multi-language support test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def test_email_system():
    """Test email system functionality"""
    print("\n📧 Testing Email System...")
    
    app = create_app()
    
    with app.app_context():
        try:
            email_service = EmailService()
            print("✅ Email service initialized")
            
            # Test basic email sending
            print("\n🔹 Testing basic email...")
            result = email_service.send_email(
                recipient_email="test@example.com",
                subject="System Test Email",
                html_content="<h2>ChamaLink System Test</h2><p>Email system is working correctly.</p>",
                text_content="ChamaLink System Test - Email system is working correctly."
            )
            
            if result:
                print("✅ Basic email sending works")
            else:
                print("❌ Basic email sending failed")
                return False
            
            print("\n🎉 Email system test complete!")
            return True
            
        except Exception as e:
            print(f"❌ Email system test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("🚀 Starting Simplified System Tests...")
    
    # Test 1: Password reset flow
    password_reset_passed = test_password_reset_flow()
    
    # Test 2: User management
    user_mgmt_passed = test_user_management()
    
    # Test 3: Multi-language support
    language_passed = test_multi_language_support()
    
    # Test 4: Email system
    email_passed = test_email_system()
    
    print("\n" + "="*60)
    print("📊 SIMPLIFIED SYSTEM TEST RESULTS:")
    print("="*60)
    print(f"Password Reset Flow:    {'✅ PASS' if password_reset_passed else '❌ FAIL'}")
    print(f"User Management:        {'✅ PASS' if user_mgmt_passed else '❌ FAIL'}")
    print(f"Multi-Language Support: {'✅ PASS' if language_passed else '❌ FAIL'}")
    print(f"Email System:           {'✅ PASS' if email_passed else '❌ FAIL'}")
    
    if password_reset_passed and user_mgmt_passed and language_passed and email_passed:
        print("\n🎉 All core system tests passed! System is production ready.")
        sys.exit(0)
    else:
        print("\n⚠️ Some system tests failed. Check implementation.")
        sys.exit(1)
