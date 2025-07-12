"""
Script to create test users and scenarios for CHAMAlink testing
"""
from datetime import datetime, timedelta
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionPlan
from app.models.chama import Chama, ChamaMember
from werkzeug.security import generate_password_hash

def create_test_users():
    """Create test users with different scenarios"""
    
    app = create_app()
    with app.app_context():
        
        print("🔧 Creating test users and scenarios...")
        
        # 1. Create test user with expired free trial
        expired_user = User.query.filter_by(email='expired.trial@test.com').first()
        if not expired_user:
            expired_user = User(
                username='expired_trial',
                email='expired.trial@test.com',
                phone_number='+254701234567',
                password_hash=generate_password_hash('password123'),
                first_name='Trial',
                last_name='Expired',
                country_code='KE',
                country_name='Kenya',
                preferred_currency='KES',
                timezone='Africa/Nairobi',
                is_email_verified=True,
                created_at=datetime.utcnow() - timedelta(days=20)  # Created 20 days ago
            )
            db.session.add(expired_user)
            print("✅ Created expired trial user: expired.trial@test.com / password123")
        
        # 2. Create test user with active subscription
        active_user = User.query.filter_by(email='active.user@test.com').first()
        if not active_user:
            active_user = User(
                username='active_user',
                email='active.user@test.com',
                phone_number='+254701234568',
                password_hash=generate_password_hash('password123'),
                first_name='Active',
                last_name='User',
                country_code='TZ',
                country_name='Tanzania',
                preferred_currency='TZS',
                timezone='Africa/Dar_es_Salaam',
                is_email_verified=True,
                created_at=datetime.utcnow() - timedelta(days=5)
            )
            db.session.add(active_user)
            print("✅ Created active user: active.user@test.com / password123")
        
        # 3. Create test user from Uganda
        uganda_user = User.query.filter_by(email='uganda.user@test.com').first()
        if not uganda_user:
            uganda_user = User(
                username='uganda_user',
                email='uganda.user@test.com',
                phone_number='+256701234567',
                password_hash=generate_password_hash('password123'),
                first_name='Uganda',
                last_name='Tester',
                country_code='UG',
                country_name='Uganda',
                preferred_currency='UGX',
                timezone='Africa/Kampala',
                is_email_verified=True,
                created_at=datetime.utcnow() - timedelta(days=3)
            )
            db.session.add(uganda_user)
            print("✅ Created Uganda user: uganda.user@test.com / password123")
        
        # 4. Create international user (US)
        us_user = User.query.filter_by(email='us.user@test.com').first()
        if not us_user:
            us_user = User(
                username='us_user',
                email='us.user@test.com',
                phone_number='+1555123456',
                password_hash=generate_password_hash('password123'),
                first_name='John',
                last_name='American',
                country_code='US',
                country_name='United States',
                preferred_currency='USD',
                timezone='America/New_York',
                is_email_verified=True,
                created_at=datetime.utcnow() - timedelta(days=1)
            )
            db.session.add(us_user)
            print("✅ Created US user: us.user@test.com / password123")
        
        db.session.commit()
        
        # Create subscription plans if they don't exist
        plans = ['basic', 'classic', 'advanced', 'enterprise']
        for plan_name in plans:
            plan = SubscriptionPlan.query.filter_by(name=plan_name).first()
            if not plan:
                plan_prices = {
                    'basic': {'KES': 500, 'USD': 5, 'TZS': 11000, 'UGX': 18000},
                    'classic': {'KES': 1200, 'USD': 12, 'TZS': 26000, 'UGX': 43000},
                    'advanced': {'KES': 2500, 'USD': 25, 'TZS': 55000, 'UGX': 90000},
                    'enterprise': {'KES': 30, 'USD': 0.30, 'TZS': 65, 'UGX': 110}
                }
                
                plan = SubscriptionPlan(
                    name=plan_name,
                    display_name=plan_name.title(),
                    description=f"{plan_name.title()} plan features",
                    price_kes=plan_prices[plan_name]['KES'],
                    price_usd=plan_prices[plan_name]['USD'],
                    duration_months=1,
                    max_chamas=50 if plan_name == 'basic' else 200 if plan_name == 'classic' else 1000 if plan_name == 'advanced' else -1,
                    max_members_per_chama=50 if plan_name == 'basic' else 200 if plan_name == 'classic' else 1000 if plan_name == 'advanced' else -1,
                    features=f"{plan_name}_features"
                )
                db.session.add(plan)
                print(f"✅ Created {plan_name} subscription plan")
        
        db.session.commit()
        
        # Create expired subscription for expired_user
        basic_plan = SubscriptionPlan.query.filter_by(name='basic').first()
        if basic_plan and expired_user:
            expired_subscription = Subscription.query.filter_by(user_id=expired_user.id).first()
            if not expired_subscription:
                expired_subscription = Subscription(
                    user_id=expired_user.id,
                    plan_id=basic_plan.id,
                    start_date=datetime.utcnow() - timedelta(days=20),
                    end_date=datetime.utcnow() - timedelta(days=6),  # Expired 6 days ago
                    status='expired',
                    payment_status='pending',
                    currency='KES',
                    amount_paid=0,
                    is_trial=True
                )
                db.session.add(expired_subscription)
                print("✅ Created expired subscription for trial user")
        
        # Create active subscription for active_user
        classic_plan = SubscriptionPlan.query.filter_by(name='classic').first()
        if classic_plan and active_user:
            active_subscription = Subscription.query.filter_by(user_id=active_user.id).first()
            if not active_subscription:
                active_subscription = Subscription(
                    user_id=active_user.id,
                    plan_id=classic_plan.id,
                    start_date=datetime.utcnow() - timedelta(days=5),
                    end_date=datetime.utcnow() + timedelta(days=25),  # Active for 25 more days
                    status='active',
                    payment_status='paid',
                    currency='TZS',
                    amount_paid=26000,
                    is_trial=False
                )
                db.session.add(active_subscription)
                print("✅ Created active subscription for TZ user")
        
        db.session.commit()
        
        # Create test chamas
        if expired_user:
            test_chama = Chama.query.filter_by(name='Test Chama Expired').first()
            if not test_chama:
                test_chama = Chama(
                    name='Test Chama Expired',
                    description='Test chama for expired user testing',
                    creator_id=expired_user.id,
                    base_currency='KES',
                    multi_currency_enabled=False,
                    created_at=datetime.utcnow() - timedelta(days=18)
                )
                db.session.add(test_chama)
                db.session.commit()
                
                # Add user as member
                member = ChamaMember(
                    user_id=expired_user.id,
                    chama_id=test_chama.id,
                    role='creator',
                    is_active=True,
                    joined_date=datetime.utcnow() - timedelta(days=18)
                )
                db.session.add(member)
                print("✅ Created test chama for expired user")
        
        if active_user:
            active_chama = Chama.query.filter_by(name='Tanzania Active Chama').first()
            if not active_chama:
                active_chama = Chama(
                    name='Tanzania Active Chama',
                    description='Active chama in Tanzania',
                    creator_id=active_user.id,
                    base_currency='TZS',
                    multi_currency_enabled=True,
                    created_at=datetime.utcnow() - timedelta(days=4)
                )
                db.session.add(active_chama)
                db.session.commit()
                
                # Add user as member
                member = ChamaMember(
                    user_id=active_user.id,
                    chama_id=active_chama.id,
                    role='creator',
                    is_active=True,
                    joined_date=datetime.utcnow() - timedelta(days=4)
                )
                db.session.add(member)
                print("✅ Created active chama for TZ user")
        
        db.session.commit()
        
        print("\n🎉 Test data creation completed!")
        print("\n📋 Test Users Created:")
        print("1. Expired Trial User:")
        print("   Email: expired.trial@test.com")
        print("   Password: password123")
        print("   Status: Free trial expired 6 days ago")
        print("   Country: Kenya (KES)")
        print("   Should prompt for payment")
        print()
        print("2. Active User:")
        print("   Email: active.user@test.com") 
        print("   Password: password123")
        print("   Status: Active classic subscription")
        print("   Country: Tanzania (TZS)")
        print()
        print("3. Uganda User:")
        print("   Email: uganda.user@test.com")
        print("   Password: password123")
        print("   Country: Uganda (UGX)")
        print()
        print("4. US User:")
        print("   Email: us.user@test.com")
        print("   Password: password123")
        print("   Country: United States (USD)")

if __name__ == '__main__':
    create_test_users()
