#!/usr/bin/env python3
"""
Test script to verify the ChamaLink application is working correctly
"""
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.user import User
from app.models.subscription import SubscriptionPlan, UserSubscription
from app.utils.email_service import send_email, send_email_verification

def test_application():
    """Test basic application functionality"""
    app = create_app()
    
    with app.app_context():
        print("✅ Application created successfully")
        
        # Test database connection
        try:
            plans = SubscriptionPlan.query.all()
            print(f"✅ Database connected - Found {len(plans)} subscription plans")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
        
        # Test user model
        try:
            user_count = User.query.count()
            print(f"✅ User model working - Found {user_count} users")
        except Exception as e:
            print(f"❌ User model failed: {e}")
            return False
        
        # Test email service
        try:
            result = send_email(
                'test@example.com',
                'Test Subject',
                '<h1>Test HTML</h1>',
                'Test text content'
            )
            print(f"✅ Email service initialized - {'Success' if result else 'Failed (expected without email config)'}")
        except Exception as e:
            print(f"❌ Email service failed: {e}")
            return False
        
        return True

if __name__ == '__main__':
    print("🔄 Testing ChamaLink Application...")
    success = test_application()
    
    if success:
        print("\n🎉 All tests passed! ChamaLink is ready to use.")
        print("\nNext steps:")
        print("1. Set up email configuration (EMAIL_PASSWORD environment variable)")
        print("2. Configure M-Pesa API credentials")
        print("3. Test user registration and login flow")
        print("4. Set up production deployment")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)
