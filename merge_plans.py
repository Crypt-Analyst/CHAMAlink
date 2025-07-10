#!/usr/bin/env python3
"""Script to merge SACCO/NGO plan features into Enterprise plan"""

import os
import sys
from app import create_app, db
from app.models.enterprise import EnterpriseSubscriptionPlan, PlanType

def merge_sacco_into_enterprise():
    """Merge SACCO/NGO plan features into Enterprise plan and remove SACCO/NGO plan"""
    app = create_app()
    
    with app.app_context():
        # Get the current plans
        sacco_plan = EnterpriseSubscriptionPlan.query.filter_by(plan_type=PlanType.SACCO_NGO).first()
        enterprise_plan = EnterpriseSubscriptionPlan.query.filter_by(plan_type=PlanType.ENTERPRISE).first()
        
        if not sacco_plan:
            print("❌ SACCO/NGO plan not found")
            return
            
        if not enterprise_plan:
            print("❌ Enterprise plan not found")
            return
            
        print("🔄 Merging SACCO/NGO features into Enterprise plan...")
        
        # Update Enterprise plan with SACCO/NGO features
        enterprise_plan.description = "Complete enterprise solution for large organizations, SACCOs, and NGOs with flexible pricing options"
        enterprise_plan.price_per_member = sacco_plan.price_per_member  # KES 30
        enterprise_plan.base_service_fee = sacco_plan.base_service_fee  # KES 1000
        enterprise_plan.training_fee_per_day = sacco_plan.training_fee_per_day  # KES 500
        
        # Ensure Enterprise plan has all premium features
        enterprise_plan.has_dedicated_manager = True
        enterprise_plan.has_training_support = True
        enterprise_plan.has_custom_branding = True
        enterprise_plan.has_white_labeling = True
        enterprise_plan.has_automated_backups = True
        enterprise_plan.has_audit_logs = True
        
        # Set max chamas to unlimited (using high number)
        enterprise_plan.max_chamas = 999
        
        print("✅ Enterprise plan updated with SACCO/NGO features:")
        print(f"   - Per member pricing: KES {enterprise_plan.price_per_member}")
        print(f"   - Base service fee: KES {enterprise_plan.base_service_fee}")
        print(f"   - Training fee: KES {enterprise_plan.training_fee_per_day}")
        print(f"   - Enhanced features enabled")
        
        # Deactivate the SACCO/NGO plan
        sacco_plan.is_active = False
        print(f"✅ SACCO/NGO plan deactivated")
        
        # Commit changes
        try:
            db.session.commit()
            print("✅ Changes saved to database")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error saving changes: {e}")
            return
            
        # Verify the changes
        print(f"\n📋 Updated Enterprise Plan:")
        print(f"   Name: {enterprise_plan.name}")
        print(f"   Description: {enterprise_plan.description}")
        print(f"   Price Monthly: KES {enterprise_plan.price_monthly}")
        print(f"   Price Per Member: KES {enterprise_plan.price_per_member}")
        print(f"   Base Service Fee: KES {enterprise_plan.base_service_fee}")
        print(f"   Training Fee: KES {enterprise_plan.training_fee_per_day}")

if __name__ == '__main__':
    merge_sacco_into_enterprise()
