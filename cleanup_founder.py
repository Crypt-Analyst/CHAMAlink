#!/usr/bin/env python3
"""
Clean up duplicate users and fix founder
"""

from app import create_app, db
from app.models.user import User

def cleanup_and_fix_founder():
    app = create_app()
    
    with app.app_context():
        print("🔍 Current users:")
        users = User.query.all()
        for user in users:
            print(f"ID {user.id}: {user.email} | {user.username} | Super Admin: {user.is_super_admin}")
        
        # Delete the duplicate user with wrong email
        duplicate_user = User.query.filter_by(email='bilfordderick@gmail.com').first()
        if duplicate_user:
            print(f"\n🗑️  Deleting duplicate user: {duplicate_user.email}")
            try:
                db.session.delete(duplicate_user)
                db.session.commit()
                print("✅ Duplicate user deleted")
            except Exception as e:
                print(f"❌ Error deleting duplicate: {e}")
                db.session.rollback()
                return False
        
        # Now update the correct user
        target_user = User.query.filter_by(email='bilfordderek917@gmail.com').first()
        if target_user:
            print(f"\n✅ Updating user: {target_user.email}")
            try:
                target_user.username = 'Bwire'
                target_user.first_name = 'Bilford'
                target_user.last_name = 'Bwire'
                target_user.phone_number = '0722206805'
                target_user.role = 'super_admin'
                target_user.is_super_admin = True
                target_user.is_founder = True
                target_user.is_email_verified = True
                target_user.is_documents_verified = True
                target_user.is_active = True
                target_user.set_password('B-wire.@1')
                
                db.session.commit()
                
                print("🎉 FOUNDER SETUP COMPLETE!")
                print("=" * 50)
                print(f"📧 Email: {target_user.email}")
                print(f"👤 Username: {target_user.username}")
                print(f"🔑 Password: B-wire.@1")
                print(f"🔰 Role: {target_user.role}")
                print(f"👑 Founder: {target_user.is_founder}")
                print(f"🛡️  Super Admin: {target_user.is_super_admin}")
                print("=" * 50)
                print("\n🚀 You can now login and access all advanced features!")
                
                return True
                
            except Exception as e:
                print(f"❌ Error updating user: {e}")
                db.session.rollback()
                return False
        else:
            print("❌ Target user not found")
            return False

if __name__ == '__main__':
    cleanup_and_fix_founder()
