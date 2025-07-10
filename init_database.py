#!/usr/bin/env python3
"""
Database initialization script for ChamaLink
Creates all necessary tables and initial data
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.chama import Chama
from app.models.enterprise import EnterpriseSubscriptionPlan, PlanType
from datetime import datetime

def init_database():
    """Initialize database with all tables and default data"""
    print("🔧 INITIALIZING CHAMALINK DATABASE")
    print("=" * 40)
    
    try:
        app = create_app()
        with app.app_context():
            print("1. Testing database connection...")
            try:
                # Test connection
                result = db.engine.execute('SELECT version()')
                version = result.fetchone()[0]
                print(f"✅ Connected to PostgreSQL: {version[:50]}...")
            except Exception as e:
                print(f"❌ Database connection failed: {e}")
                return False
            
            print("2. Creating all tables...")
            try:
                db.create_all()
                print("✅ All tables created successfully")
            except Exception as e:
                print(f"❌ Table creation failed: {e}")
                return False
            
            print("3. Checking table status...")
            try:
                inspector = db.inspect(db.engine)
                tables = inspector.get_table_names()
                print(f"✅ Found {len(tables)} tables: {', '.join(tables[:5])}...")
            except Exception as e:
                print(f"❌ Table inspection failed: {e}")
            
            print("4. Creating default subscription plans...")
            try:
                # Check if plans already exist
                plan_count = EnterpriseSubscriptionPlan.query.count()
                if plan_count == 0:
                    # Create default plans
                    plans = [
                        EnterpriseSubscriptionPlan(
                            name="Basic Plan",
                            plan_type=PlanType.BASIC,
                            price_monthly=200.0,
                            max_chamas=1,
                            max_members_per_chama=50,
                            has_sms_notifications=True,
                            is_active=True,
                            created_at=datetime.utcnow()
                        ),
                        EnterpriseSubscriptionPlan(
                            name="Advanced Plan", 
                            plan_type=PlanType.ADVANCED,
                            price_monthly=350.0,
                            max_chamas=3,
                            max_members_per_chama=200,
                            has_sms_notifications=True,
                            has_advanced_reporting=True,
                            has_api_access=True,
                            is_active=True,
                            created_at=datetime.utcnow()
                        ),
                        EnterpriseSubscriptionPlan(
                            name="Enterprise Plan",
                            plan_type=PlanType.ENTERPRISE,
                            price_monthly=0.0,  # Custom pricing
                            max_chamas=-1,  # Unlimited
                            max_members_per_chama=-1,  # Unlimited
                            has_sms_notifications=True,
                            has_advanced_reporting=True,
                            has_api_access=True,
                            has_white_labeling=True,
                            has_priority_support=True,
                            is_active=True,
                            created_at=datetime.utcnow()
                        )
                    ]
                    
                    for plan in plans:
                        db.session.add(plan)
                    
                    db.session.commit()
                    print(f"✅ Created {len(plans)} default subscription plans")
                else:
                    print(f"✅ Found {plan_count} existing subscription plans")
                    
            except Exception as e:
                print(f"❌ Subscription plan creation failed: {e}")
                db.session.rollback()
            
            print("5. Testing model queries...")
            try:
                user_count = User.query.count()
                chama_count = Chama.query.count()
                plan_count = EnterpriseSubscriptionPlan.query.count()
                
                print(f"✅ Users: {user_count}")
                print(f"✅ Chamas: {chama_count}")
                print(f"✅ Subscription Plans: {plan_count}")
                
            except Exception as e:
                print(f"❌ Model query failed: {e}")
            
            print("\n🎉 Database initialization completed successfully!")
            print("✅ ChamaLink database is ready for use")
            return True
            
    except Exception as e:
        print(f"❌ Critical error during initialization: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_database()
    if success:
        print("\n🚀 You can now start the ChamaLink application")
    else:
        print("\n🔧 Please fix the errors above before starting the application")
        sys.exit(1)
