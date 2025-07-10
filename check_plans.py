#!/usr/bin/env python3
"""Script to check current plans and merge SACCO/NGO with Enterprise"""

import os
import sys
from app import create_app, db
from app.models.enterprise import EnterpriseSubscriptionPlan, PlanType

def check_current_plans():
    """Check current plans in database"""
    app = create_app()
    
    with app.app_context():
        plans = EnterpriseSubscriptionPlan.query.all()
        
        print("Current Plans in Database:")
        print("=" * 50)
        
        for plan in plans:
            print(f"\nPlan: {plan.name}")
            print(f"  Type: {plan.plan_type.value}")
            print(f"  Active: {plan.is_active}")
            print(f"  Price Monthly: {plan.price_monthly}")
            print(f"  Price Per Member: {plan.price_per_member}")
            print(f"  Base Service Fee: {plan.base_service_fee}")
            print(f"  Training Fee: {plan.training_fee_per_day}")
            print(f"  Max Chamas: {plan.max_chamas}")
            print(f"  Max Members: {plan.max_members_per_chama}")
            print(f"  Features: SMS={plan.has_sms_notifications}, API={plan.has_api_access}")
            
        # Check for SACCO/NGO plan specifically
        sacco_plan = EnterpriseSubscriptionPlan.query.filter_by(plan_type=PlanType.SACCO_NGO).first()
        enterprise_plan = EnterpriseSubscriptionPlan.query.filter_by(plan_type=PlanType.ENTERPRISE).first()
        
        if sacco_plan:
            print(f"\n📋 SACCO/NGO Plan Found: {sacco_plan.name}")
            print(f"   Features to merge into Enterprise plan:")
            print(f"   - Per member pricing: KES {sacco_plan.price_per_member}")
            print(f"   - Base service fee: KES {sacco_plan.base_service_fee}")
            print(f"   - Training fee: KES {sacco_plan.training_fee_per_day}")
            
        if enterprise_plan:
            print(f"\n🏢 Enterprise Plan Found: {enterprise_plan.name}")
            print(f"   Current features - will be enhanced with SACCO/NGO features")

if __name__ == '__main__':
    check_current_plans()
