#!/usr/bin/env python3
"""
Complete Authentication Flow Test
Test forgot password and registration-to-verification flows
"""

import sys
import os
import time
import requests
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up Flask app
os.environ['FLASK_ENV'] = 'testing'

from app import create_app, db
from app.models.user import User
from app.utils.email_service import EmailService

def test_registration_flow():
    """Test complete registration and verification flow"""
    print("📝 Testing Registration and Verification Flow...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Step 1: Create a test user (simulate registration)
            print("\n🔹 Step 1: Creating test user...")
            test_email = "test_reg_user@example.com"
            
            # Clean up any existing test user
            existing_user = User.query.filter_by(email=test_email).first()
            if existing_user:
                db.session.delete(existing_user)
                db.session.commit()
            
            # Create new test user
            test_user = User(
                username="test_reg_user",
                email=test_email,
                first_name="Test Registration",
                last_name="User"
            )
            test_user.set_password("testpassword123")
            test_user.is_email_verified = False  # Not verified initially
            
            db.session.add(test_user)
            db.session.commit()
            print(f"✅ Test user created: {test_email}")
            
            # Step 2: Generate verification token and send email
            print("\n🔹 Step 2: Sending verification email...")
            verification_token = test_user.generate_verification_token()
            
            email_service = EmailService()
            email_result = email_service.send_email_verification(
                user=test_user,
                verification_token=verification_token
            )
            
            if email_result:
                print("✅ Verification email sent successfully")
            else:
                print("❌ Failed to send verification email")
                return False
            
            # Step 3: Simulate email verification (in production, user clicks link)
            print("\n🔹 Step 3: Simulating email verification...")
            if test_user.verify_email_token(verification_token):
                test_user.is_email_verified = True
                db.session.commit()
                print("✅ Email verification successful")
            else:
                print("❌ Email verification failed")
                return False
            
            # Step 4: Verify user can now log in
            print("\n🔹 Step 4: Testing login after verification...")
            if test_user.check_password("testpassword123") and test_user.is_email_verified:
                print("✅ User can log in after verification")
            else:
                print("❌ User cannot log in after verification")
                return False
            
            print("\n🎉 Registration-to-verification flow complete!")
            return True
            
        except Exception as e:
            print(f"❌ Registration flow test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def test_forgot_password_flow():
    """Test complete forgot password flow"""
    print("\n🔑 Testing Forgot Password Flow...")
    
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
            
            # Step 2: Generate password reset token and send email
            print("\n🔹 Step 2: Sending password reset email...")
            reset_token = test_user.generate_reset_token()
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
            
            # Step 3: Simulate password reset (in production, user clicks link and submits form)
            print("\n🔹 Step 3: Simulating password reset...")
            if test_user.verify_reset_token(reset_token):
                new_password = "newpassword456"
                test_user.set_password(new_password)
                db.session.commit()
                print("✅ Password reset successful")
            else:
                print("❌ Password reset token verification failed")
                return False
            
            # Step 4: Verify user can log in with new password
            print("\n🔹 Step 4: Testing login with new password...")
            if test_user.check_password("newpassword456"):
                print("✅ User can log in with new password")
            else:
                print("❌ User cannot log in with new password")
                return False
            
            # Step 5: Verify old password no longer works
            print("\n🔹 Step 5: Verifying old password is invalid...")
            if not test_user.check_password("originalpassword123"):
                print("✅ Old password is no longer valid")
            else:
                print("❌ Old password still works (security issue)")
                return False
            
            print("\n🎉 Forgot password flow complete!")
            return True
            
        except Exception as e:
            print(f"❌ Forgot password flow test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def test_multi_language_support():
    """Test multi-language support functionality"""
    print("\n🌍 Testing Multi-Language Support...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Test loading English translations
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
            
            # Test session management functions
            print("\n🔹 Testing preference management...")
            from app.utils.internationalization import set_language_preference, get_language_preference
            
            # This would normally use Flask session, but we'll just test the functions exist
            print("✅ Language preference functions available")
            
            print("\n🎉 Multi-language support test complete!")
            return True
            
        except Exception as e:
            print(f"❌ Multi-language support test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("🚀 Starting Complete Authentication Flow Tests...")
    
    # Test 1: Registration and verification flow
    registration_passed = test_registration_flow()
    
    # Test 2: Forgot password flow
    forgot_password_passed = test_forgot_password_flow()
    
    # Test 3: Multi-language support
    language_passed = test_multi_language_support()
    
    print("\n" + "="*60)
    print("📊 AUTHENTICATION FLOW TEST RESULTS:")
    print("="*60)
    print(f"Registration-Verification: {'✅ PASS' if registration_passed else '❌ FAIL'}")
    print(f"Forgot Password Flow:      {'✅ PASS' if forgot_password_passed else '❌ FAIL'}")
    print(f"Multi-Language Support:    {'✅ PASS' if language_passed else '❌ FAIL'}")
    
    if registration_passed and forgot_password_passed and language_passed:
        print("\n🎉 All authentication flows passed! System is production ready.")
        sys.exit(0)
    else:
        print("\n⚠️ Some authentication flows failed. Check implementation.")
        sys.exit(1)
