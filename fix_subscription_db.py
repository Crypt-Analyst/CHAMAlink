#!/usr/bin/env python3
"""
Fix subscription database schema issues
- Add missing pricing_id column to subscription_payments
- Create subscription_plan_pricing table if missing
"""

from app import create_app, db
from app.models.subscription import SubscriptionPlan, SubscriptionPlanPricing, SubscriptionPayment
import os

def fix_subscription_schema():
    app = create_app()
    with app.app_context():
        try:
            # Check if subscription_plan_pricing table exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print("📋 Current tables:", tables)
            
            # Create tables if they don't exist
            if 'subscription_plan_pricing' not in tables:
                print("🔧 Creating subscription_plan_pricing table...")
                db.create_all()
                print("✅ Tables created successfully!")
            
            # Check if pricing_id column exists in subscription_payments
            if 'subscription_payments' in tables:
                columns = [col['name'] for col in inspector.get_columns('subscription_payments')]
                print(f"📋 subscription_payments columns: {columns}")
                
                if 'pricing_id' not in columns:
                    print("🔧 Adding missing columns to subscription_payments...")
                    from sqlalchemy import text
                    
                    # Add the missing columns
                    db.session.execute(text("ALTER TABLE subscription_payments ADD COLUMN pricing_id INTEGER;"))
                    db.session.execute(text("ALTER TABLE subscription_payments ADD COLUMN months_purchased INTEGER DEFAULT 1;"))
                    db.session.execute(text("ALTER TABLE subscription_payments ADD COLUMN bonus_months INTEGER DEFAULT 0;"))
                    db.session.commit()
                    print("✅ Missing columns added successfully!")
                else:
                    print("✅ All required columns already exist!")
            
            # Initialize pricing plans if table is empty
            pricing_count = SubscriptionPlanPricing.query.count()
            if pricing_count == 0:
                print("🔧 Initializing subscription pricing plans...")
                
                # Get existing plans
                basic_plan = SubscriptionPlan.query.filter_by(name='basic').first()
                classic_plan = SubscriptionPlan.query.filter_by(name='classic').first()
                advanced_plan = SubscriptionPlan.query.filter_by(name='advanced').first()
                
                pricing_options = []
                
                if basic_plan:
                    pricing_options.extend([
                        SubscriptionPlanPricing(plan_id=basic_plan.id, months=1, price=200.0, discount_percent=0),
                        SubscriptionPlanPricing(plan_id=basic_plan.id, months=3, price=570.0, discount_percent=5),
                        SubscriptionPlanPricing(plan_id=basic_plan.id, months=6, price=1080.0, discount_percent=10),
                        SubscriptionPlanPricing(plan_id=basic_plan.id, months=12, price=2000.0, discount_percent=17),
                    ])
                
                if classic_plan:
                    pricing_options.extend([
                        SubscriptionPlanPricing(plan_id=classic_plan.id, months=1, price=250.0, discount_percent=0),
                        SubscriptionPlanPricing(plan_id=classic_plan.id, months=3, price=712.5, discount_percent=5),
                        SubscriptionPlanPricing(plan_id=classic_plan.id, months=6, price=1350.0, discount_percent=10),
                        SubscriptionPlanPricing(plan_id=classic_plan.id, months=12, price=2500.0, discount_percent=17),
                    ])
                
                if advanced_plan:
                    pricing_options.extend([
                        SubscriptionPlanPricing(plan_id=advanced_plan.id, months=1, price=500.0, discount_percent=0),
                        SubscriptionPlanPricing(plan_id=advanced_plan.id, months=3, price=1425.0, discount_percent=5),
                        SubscriptionPlanPricing(plan_id=advanced_plan.id, months=6, price=2700.0, discount_percent=10),
                        SubscriptionPlanPricing(plan_id=advanced_plan.id, months=12, price=5000.0, discount_percent=17),
                    ])
                
                for pricing in pricing_options:
                    db.session.add(pricing)
                
                db.session.commit()
                print(f"✅ Added {len(pricing_options)} pricing options!")
            else:
                print(f"✅ Pricing plans already exist: {pricing_count} options")
            
            print("\n🎉 Database schema fix completed successfully!")
            print("📱 You can now restart the application.")
            
        except Exception as e:
            print(f"❌ Error fixing database schema: {e}")
            db.session.rollback()

if __name__ == '__main__':
    fix_subscription_schema()
