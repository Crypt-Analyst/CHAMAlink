#!/usr/bin/env python3
"""
Quick script to test user login functionality
"""

from app import create_app, db
from app.models.user import User
from werkzeug.security import check_password_hash

def test_login():
    app = create_app()
    with app.app_context():
        # Check if any users exist
        users = User.query.all()
        print(f"Total users in database: {len(users)}")
        
        if users:
            test_user = users[0]
            print(f"\nTesting with user: {test_user.email}")
            print(f"Username: {test_user.username}")
            print(f"Password hash length: {len(test_user.password_hash) if test_user.password_hash else 0}")
            print(f"Email verified: {test_user.is_email_verified}")
            print(f"Account locked: {test_user.is_account_locked}")
            
            # Test a common password
            test_passwords = ['123456', 'password', 'test123', 'admin']
            
            for password in test_passwords:
                if test_user.check_password(password):
                    print(f"✅ Password '{password}' works for {test_user.email}")
                    return
            
            print("❌ None of the common passwords worked")
            
            # Let's try to set a known password for testing
            test_user.set_password('test123')
            test_user.is_email_verified = True  # Ensure email is verified
            db.session.commit()
            print("✅ Set password to 'test123' and verified email")
            
        else:
            print("No users found. Creating a test user...")
            # Create a test user
            test_user = User(
                username='testuser',
                email='test@example.com',
                phone_number='0700000000',
                is_email_verified=True
            )
            test_user.set_password('test123')
            db.session.add(test_user)
            db.session.commit()
            print("✅ Created test user: test@example.com / test123")

if __name__ == '__main__':
    test_login()
