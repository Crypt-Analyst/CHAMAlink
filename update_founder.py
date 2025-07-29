#!/usr/bin/env python3
"""
Update founder user with specific details
"""

from app import create_app, db
from app.models.user import User
from datetime import datetime

def update_founder():
    app = create_app()
    
    with app.app_context():
        # Find the existing founder user
        founder = User.query.filter_by(email='founder@chamalink.com').first()
        
        if founder:
            print(f'✅ Found existing founder, updating details...')
            
            # Update with new details
            founder.username = 'Bwire'
            founder.email = 'bilfordderick@gmail.com'
            founder.phone_number = '0722206805'
            founder.first_name = 'Bilford'
            founder.last_name = 'Bwire'
            founder.role = 'super_admin'
            founder.is_super_admin = True
            founder.is_founder = True  # Mark as founder
            founder.is_email_verified = True
            founder.is_documents_verified = True
            founder.is_active = True
            
            # Set new password
            founder.set_password('B-wire.@1')
            
            try:
                db.session.commit()
                
                print('🎉 FOUNDER USER UPDATED SUCCESSFULLY!')
                print('=' * 60)
                print(f'👤 Username: {founder.username}')
                print(f'📧 Email: {founder.email}')
                print(f'📱 Phone: {founder.phone_number}')
                print(f'🏷️  Full Name: {founder.first_name} {founder.last_name}')
                print(f'🔑 Password: B-wire.@1')
                print(f'🔰 Role: {founder.role}')
                print(f'👑 Founder Status: {founder.is_founder}')
                print(f'🛡️  Super Admin: {founder.is_super_admin}')
                print(f'🆔 ID: {founder.id}')
                print('=' * 60)
                print('✅ This user is now protected and cannot be deleted!')
                
                return founder
                
            except Exception as e:
                print(f'❌ Error updating founder: {e}')
                db.session.rollback()
                return None
        else:
            # Create new founder user if doesn't exist
            print('Creating new founder user...')
            founder = User(
                username='Bwire',
                email='bilfordderick@gmail.com',
                phone_number='0722206805',
                first_name='Bilford',
                last_name='Bwire',
                role='super_admin',
                is_super_admin=True,
                is_founder=True,
                is_email_verified=True,
                is_documents_verified=True,
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            founder.set_password('B-wire.@1')
            
            try:
                db.session.add(founder)
                db.session.commit()
                
                print('🎉 NEW FOUNDER USER CREATED!')
                print('=' * 60)
                print(f'👤 Username: {founder.username}')
                print(f'📧 Email: {founder.email}')
                print(f'📱 Phone: {founder.phone_number}')
                print(f'🏷️  Full Name: {founder.first_name} {founder.last_name}')
                print(f'🔑 Password: B-wire.@1')
                print(f'🔰 Role: {founder.role}')
                print(f'👑 Founder Status: {founder.is_founder}')
                print(f'🛡️  Super Admin: {founder.is_super_admin}')
                print(f'🆔 ID: {founder.id}')
                print('=' * 60)
                print('✅ This user is protected and cannot be deleted!')
                
                return founder
                
            except Exception as e:
                print(f'❌ Error creating founder: {e}')
                db.session.rollback()
                return None

if __name__ == '__main__':
    update_founder()
