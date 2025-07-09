#!/usr/bin/env python3
"""
Quick script to create a user account
"""
from app import create_app, db
from app.models.user import User

def create_user():
    app = create_app()
    
    with app.app_context():
        # Get user input
        username = input("Enter username: ")
        email = input("Enter email: ")
        password = input("Enter password: ")
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"❌ User with email {email} already exists!")
            return
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        # Save to database
        db.session.add(user)
        db.session.commit()
        
        print(f"✅ User '{username}' created successfully!")
        print(f"📧 Email: {email}")
        print(f"🔑 You can now login with these credentials")

if __name__ == "__main__":
    create_user()
