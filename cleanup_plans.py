#!/usr/bin/env python3
"""
Database cleanup script for ChamaLink subscription plans
Removes duplicate and inconsistent pricing plans
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.enterprise import EnterpriseSubscriptionPlan, PlanType, EnterpriseBillingType

def cleanup_subscription_plans():
    """Clean up duplicate and inconsistent subscription plans"""
    print("🧹 Starting subscription plans cleanup...")
    
    # Get all plans
    all_plans = EnterpriseSubscriptionPlan.query.all()
    print(f"📊 Found {len(all_plans)} total plans in database")
    
    # Group by name and find duplicates
    plan_groups = {}
    for plan in all_plans:
        name_key = plan.name.lower().strip()
        if name_key not in plan_groups:
            plan_groups[name_key] = []
        plan_groups[name_key].append(plan)
    
    print(f"📈 Found {len(plan_groups)} unique plan names")
    
    # Remove duplicates and keep the best version
    plans_to_delete = []
    
    for name_key, plans in plan_groups.items():
        if len(plans) > 1:
            print(f"🔍 Found {len(plans)} plans with name '{name_key}':")
            for i, plan in enumerate(plans):
                print(f"  {i+1}. ID: {plan.id}, Price: {plan.price_monthly}, Active: {plan.is_active}")
            
            # Sort by: active status first, then by ID (assuming newer is better)
            plans.sort(key=lambda p: (p.is_active, p.id), reverse=True)
            
            # Keep the first (best) plan, mark others for deletion
            keep_plan = plans[0]
            delete_plans = plans[1:]
            
            print(f"  ✅ Keeping plan ID {keep_plan.id}")
            for del_plan in delete_plans:
                print(f"  ❌ Marking plan ID {del_plan.id} for deletion")
                plans_to_delete.append(del_plan)
    
    # Also check for plans with invalid data
    for plan in all_plans:
        if plan.price_monthly < 0:
            print(f"❌ Found plan with negative price: ID {plan.id}")
            plans_to_delete.append(plan)
        
        if not plan.name or plan.name.strip() == "":
            print(f"❌ Found plan with empty name: ID {plan.id}")
            plans_to_delete.append(plan)
    
    # Remove duplicates from deletion list
    plans_to_delete = list(set(plans_to_delete))
    
    print(f"\n🗑️  Total plans to delete: {len(plans_to_delete)}")
    
    if plans_to_delete:
        print("Plans to be deleted:")
        for plan in plans_to_delete:
            print(f"  - ID: {plan.id}, Name: '{plan.name}', Price: {plan.price_monthly}")
        
        confirm = input("\n❓ Do you want to proceed with deletion? (y/N): ")
        if confirm.lower() == 'y':
            for plan in plans_to_delete:
                try:
                    db.session.delete(plan)
                    print(f"✅ Deleted plan ID {plan.id}")
                except Exception as e:
                    print(f"❌ Error deleting plan ID {plan.id}: {e}")
            
            try:
                db.session.commit()
                print("✅ All changes committed to database")
            except Exception as e:
                print(f"❌ Error committing changes: {e}")
                db.session.rollback()
        else:
            print("❌ Deletion cancelled")
    
    # Show final state
    remaining_plans = EnterpriseSubscriptionPlan.query.filter_by(is_active=True).all()
    print(f"\n📊 Final active plans count: {len(remaining_plans)}")
    
    if remaining_plans:
        print("Active plans:")
        for plan in remaining_plans:
            print(f"  - {plan.name}: {plan.price_monthly} KES/month")

def create_standard_plans():
    """Create standard subscription plans if none exist"""
    print("\n🏗️  Checking for standard plans...")
    
    # Define standard plans
    standard_plans = [
        {
            'name': 'Basic Plan',
            'plan_type': PlanType.BASIC,
            'price_monthly': 200.0,
            'max_chamas': 1,
            'max_members_per_chama': 50,
            'max_loans_per_month': 10,
            'max_sms_per_month': 100,
            'has_sms_notifications': True,
            'has_advanced_reporting': False,
            'has_api_access': False,
        },
        {
            'name': 'Advanced Plan',
            'plan_type': PlanType.ADVANCED,
            'price_monthly': 350.0,
            'max_chamas': 3,
            'max_members_per_chama': 200,
            'max_loans_per_month': 50,
            'max_sms_per_month': 500,
            'has_sms_notifications': True,
            'has_advanced_reporting': True,
            'has_bulk_operations': True,
            'has_api_access': True,
        },
        {
            'name': 'Enterprise Plan',
            'plan_type': PlanType.ENTERPRISE,
            'price_monthly': 0.0,  # Custom pricing
            'max_chamas': -1,  # Unlimited
            'max_members_per_chama': -1,  # Unlimited
            'max_loans_per_month': -1,  # Unlimited
            'max_sms_per_month': -1,  # Unlimited
            'has_sms_notifications': True,
            'has_advanced_reporting': True,
            'has_bulk_operations': True,
            'has_api_access': True,
            'has_white_labeling': True,
            'has_priority_support': True,
            'has_audit_logs': True,
            'has_multi_signature': True,
            'has_automated_backups': True,
            'has_custom_branding': True,
            'has_dedicated_manager': True,
        }
    ]
    
    active_plans = EnterpriseSubscriptionPlan.query.filter_by(is_active=True).count()
    
    if active_plans < 3:
        print(f"📝 Only {active_plans} active plans found. Creating standard plans...")
        
        for plan_data in standard_plans:
            # Check if plan already exists
            existing = EnterpriseSubscriptionPlan.query.filter_by(
                name=plan_data['name'],
                is_active=True
            ).first()
            
            if not existing:
                plan = EnterpriseSubscriptionPlan(**plan_data)
                plan.is_active = True
                plan.created_at = datetime.utcnow()
                
                db.session.add(plan)
                print(f"✅ Created plan: {plan.name}")
        
        try:
            db.session.commit()
            print("✅ Standard plans created successfully")
        except Exception as e:
            print(f"❌ Error creating standard plans: {e}")
            db.session.rollback()
    else:
        print(f"✅ Found {active_plans} active plans. No need to create standard plans.")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        print("🚀 ChamaLink Database Cleanup Tool")
        print("=" * 40)
        
        cleanup_subscription_plans()
        create_standard_plans()
        
        print("\n✅ Cleanup complete!")
