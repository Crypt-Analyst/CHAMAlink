#!/usr/bin/env python3
"""
ChamaLink Setup Script
Initializes the system with default data and verifies everything is working
"""

import os
import sys
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models.subscription import SubscriptionPlan, SubscriptionPlanPricing
from app.models.enterprise import EnterpriseSubscriptionPlan, PlanType, EnterpriseBillingType
from app.models.user import User

def create_default_plans():
    """Create default subscription plans"""
    print("📋 Creating default subscription plans...")
    
    # Basic subscription plans
    plans_data = [
        {
            'name': 'Basic Plan',
            'description': 'Perfect for small chamas getting started',
            'price': 200.00,
            'max_chamas': 1,
            'max_members': 30,
            'features': {
                'sms_notifications': True,
                'basic_reporting': True,
                'member_management': True,
                'contribution_tracking': True
            }
        },
        {
            'name': 'Advanced Plan',
            'description': 'Ideal for growing chamas and SACCO branches',
            'price': 350.00,
            'max_chamas': 3,
            'max_members': 100,
            'features': {
                'sms_notifications': True,
                'advanced_reporting': True,
                'bulk_operations': True,
                'loan_management': True,
                'multi_signature': True,
                'automated_backups': True
            }
        },
        {
            'name': 'Enterprise Plan',
            'description': 'Comprehensive solution for large organizations',
            'price': 0.00,  # Custom pricing
            'max_chamas': 999,
            'max_members': 10000,
            'features': {
                'all_features': True,
                'api_access': True,
                'white_labeling': True,
                'priority_support': True,
                'dedicated_manager': True,
                'custom_branding': True
            }
        }
    ]
    
    for plan_data in plans_data:
        existing = SubscriptionPlan.query.filter_by(name=plan_data['name']).first()
        if not existing:
            plan = SubscriptionPlan(
                name=plan_data['name'],
                description=plan_data['description'],
                price=plan_data['price'],
                max_chamas=plan_data['max_chamas'],
                features=plan_data['features']
            )
            db.session.add(plan)
            print(f"  ✅ Created {plan_data['name']}")
        else:
            print(f"  ⏭️  {plan_data['name']} already exists")
    
    db.session.commit()

def create_pricing_options():
    """Create pricing options for subscription plans"""
    print("💰 Creating pricing options...")
    
    plans = SubscriptionPlan.query.all()
    
    for plan in plans:
        if plan.price > 0:  # Skip enterprise plan with custom pricing
            pricing_options = [
                {'months': 1, 'bonus_months': 0, 'discount_percent': 0},
                {'months': 3, 'bonus_months': 0, 'discount_percent': 5},
                {'months': 6, 'bonus_months': 1, 'discount_percent': 10},
                {'months': 12, 'bonus_months': 2, 'discount_percent': 15}
            ]
            
            for pricing_data in pricing_options:
                existing = SubscriptionPlanPricing.query.filter_by(
                    plan_id=plan.id,
                    months=pricing_data['months']
                ).first()
                
                if not existing:
                    total_price = plan.price * pricing_data['months']
                    discount_amount = total_price * (pricing_data['discount_percent'] / 100)
                    final_total_price = total_price - discount_amount
                    
                    pricing = SubscriptionPlanPricing(
                        plan_id=plan.id,
                        months=pricing_data['months'],
                        bonus_months=pricing_data['bonus_months'],
                        price_per_month=plan.price,
                        total_price=final_total_price,
                        discount_percentage=pricing_data['discount_percent']
                    )
                    db.session.add(pricing)
                    print(f"  ✅ Created {pricing_data['months']}M pricing for {plan.name}")
    
    db.session.commit()

def create_enterprise_plans():
    """Create enterprise subscription plans"""
    print("🏢 Creating enterprise plans...")
    
    # Create enterprise plans using the static method
    EnterpriseSubscriptionPlan.create_default_plans()
    print("  ✅ Enterprise plans created")

def create_admin_user():
    """Create a default admin user"""
    print("👤 Creating admin user...")
    
    admin_email = "admin@chamalink.com"
    existing_admin = User.query.filter_by(email=admin_email).first()
    
    if not existing_admin:
        admin = User(
            username="admin",
            email=admin_email,
            phone_number="254700000000",
            first_name="System",
            last_name="Administrator",
            is_super_admin=True,
            is_email_verified=True,
            is_active=True
        )
        admin.set_password("admin123")  # Change this in production!
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"  ✅ Admin user created: {admin_email} / admin123")
        print("  ⚠️  IMPORTANT: Change the admin password before production!")
    else:
        print("  ⏭️  Admin user already exists")

def verify_system():
    """Verify that all components are working"""
    print("🔍 Verifying system components...")
    
    # Check database connection
    try:
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        print("  ✅ Database connection working")
    except Exception as e:
        print(f"  ❌ Database connection failed: {e}")
        return False
    
    # Check subscription plans
    plan_count = SubscriptionPlan.query.count()
    if plan_count >= 3:
        print(f"  ✅ Subscription plans created: {plan_count}")
    else:
        print(f"  ❌ Not enough subscription plans: {plan_count}")
        return False
    
    # Check enterprise plans
    enterprise_count = EnterpriseSubscriptionPlan.query.count()
    if enterprise_count >= 4:
        print(f"  ✅ Enterprise plans created: {enterprise_count}")
    else:
        print(f"  ❌ Not enough enterprise plans: {enterprise_count}")
        return False
    
    # Check pricing options
    pricing_count = SubscriptionPlanPricing.query.count()
    if pricing_count >= 8:  # At least 4 pricing options for 2 paid plans
        print(f"  ✅ Pricing options created: {pricing_count}")
    else:
        print(f"  ❌ Not enough pricing options: {pricing_count}")
        return False
    
    print("  ✅ All system components verified")
    return True

def setup_environment():
    """Check and setup environment variables"""
    print("🔧 Checking environment setup...")
    
    required_vars = [
        'SECRET_KEY',
        'MPESA_CONSUMER_KEY',
        'MPESA_CONSUMER_SECRET',
        'MPESA_PASSKEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"  ⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("  📄 Please copy .env.example to .env and fill in your values")
        return False
    else:
        print("  ✅ Environment variables configured")
        return True

def main():
    """Main setup function"""
    print("🚀 ChamaLink Setup Script")
    print("=" * 50)
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        try:
            # Setup steps
            setup_environment()
            
            print("\n📊 Setting up database...")
            db.create_all()
            print("  ✅ Database tables created")
            
            create_default_plans()
            create_pricing_options()
            create_enterprise_plans()
            create_admin_user()
            
            print("\n🔍 Verifying setup...")
            if verify_system():
                print("\n🎉 Setup completed successfully!")
                print("\n📋 Next steps:")
                print("  1. Configure your environment variables (.env file)")
                print("  2. Set up M-Pesa credentials with Safaricom")
                print("  3. Test payments with small amounts")
                print("  4. Run: python test_system.py")
                print("  5. Deploy to production")
                
                print("\n🔑 Default admin login:")
                print("  Email: admin@chamalink.com")
                print("  Password: admin123")
                print("  ⚠️  CHANGE PASSWORD BEFORE PRODUCTION!")
                
                return True
            else:
                print("\n❌ Setup verification failed!")
                return False
                
        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
