#!/usr/bin/env python3
"""
Create founder/super admin user for ChamaLink
"""

from app import create_app, db
from app.models.user import User
from datetime import datetime

def create_founder():
    app = create_app()
    
    with app.app_context():
        # Check if founder already exists
        founder = User.query.filter_by(email='founder@chamalink.com').first()
        
        if founder:
            print(f'✅ Founder already exists!')
            print(f'Email: {founder.email}')
            print(f'Username: {founder.username}')
            print(f'Role: {founder.role}')
            print(f'Super Admin: {founder.is_super_admin}')
            print(f'ID: {founder.id}')
            return founder
        
        # Create new founder user
        founder = User(
            username='founder',
            email='founder@chamalink.com',
            phone_number='+254700000000',
            first_name='ChamaLink',
            last_name='Founder',
            role='super_admin',
            is_super_admin=True,
            is_email_verified=True,
            is_documents_verified=True,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # Set password
        founder.set_password('founder123')
        
        try:
            db.session.add(founder)
            db.session.commit()
            
            print('🎉 FOUNDER USER CREATED SUCCESSFULLY!')
            print('=' * 50)
            print(f'📧 Email: founder@chamalink.com')
            print(f'🔑 Password: founder123')
            print(f'👤 Username: founder')
            print(f'🔰 Role: Super Admin')
            print(f'🆔 ID: {founder.id}')
            print('=' * 50)
            print('This user has permanent founder status and cannot be deleted!')
            
            return founder
            
        except Exception as e:
            print(f'❌ Error creating founder: {e}')
            db.session.rollback()
            return None

if __name__ == '__main__':
    create_founder()
