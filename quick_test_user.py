"""
Quick test user creation script
"""
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app, db
    from app.models.user import User
    from werkzeug.security import generate_password_hash
    
    print("Creating test user with expired trial...")
    
    app = create_app()
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Check if test user already exists
        test_user = User.query.filter_by(email='expired.trial@test.com').first()
        if test_user:
            print("✅ Test user already exists: expired.trial@test.com")
        else:
            # Create test user
            test_user = User(
                username='expired_trial',
                email='expired.trial@test.com',
                phone_number='+254701234567',
                password_hash=generate_password_hash('password123'),
                first_name='Trial',
                last_name='Expired',
                country_code='KE',
                country_name='Kenya',
                preferred_currency='KES',
                is_email_verified=True,
                created_at=datetime.utcnow() - timedelta(days=20)  # Created 20 days ago
            )
            
            db.session.add(test_user)
            db.session.commit()
            print("✅ Created test user: expired.trial@test.com / password123")
        
        print("\n🎯 Test Account Details:")
        print("Email: expired.trial@test.com")
        print("Password: password123")
        print("Status: Free trial should be expired")
        print("Country: Kenya (KES currency)")
        print("\nUse this account to test payment functionality!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
