"""
Script to make a user super admin (founder access)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    # Find user by email (replace with your actual email)
    user_email = "bilfordbwire@gmail.com"  # Your founder email
    user = User.query.filter_by(email=user_email).first()
    
    if user:
        user.is_super_admin = True
        user.is_email_verified = True  # Also verify email
        db.session.commit()
        print(f"✅ User {user.username} ({user.email}) is now a super admin with founder access!")
        print(f"🎯 You can now access the founder dashboard at /founder-dashboard")
    else:
        print(f"❌ User with email {user_email} not found")
        print("Available users:")
        users = User.query.all()
        for u in users:
            print(f"  - {u.username} ({u.email})")
