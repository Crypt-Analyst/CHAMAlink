#!/usr/bin/env python3
"""Update Enterprise plan description for broader scope"""

import os
import sys
from app import create_app, db
from app.models.enterprise import EnterpriseSubscriptionPlan, PlanType

def update_enterprise_description():
    """Update Enterprise plan description to include Government and large organizations"""
    app = create_app()
    
    with app.app_context():
        # Get the Enterprise plan
        enterprise_plan = EnterpriseSubscriptionPlan.query.filter_by(plan_type=PlanType.ENTERPRISE).first()
        
        if not enterprise_plan:
            print("❌ Enterprise plan not found")
            return
            
        print("🔄 Updating Enterprise plan description...")
        
        # Update description
        old_description = enterprise_plan.description
        enterprise_plan.description = "Enterprise solution for SACCOs, NGOs, Government agencies, and large organizations with flexible per-member pricing"
        
        try:
            db.session.commit()
            print("✅ Enterprise plan description updated successfully")
            print(f"Old: {old_description}")
            print(f"New: {enterprise_plan.description}")
            
            # Test feature list
            features = enterprise_plan.get_feature_list()
            print(f"\n📋 Updated features ({len(features)}):")
            for i, feature in enumerate(features[:10], 1):
                print(f"   {i}. {feature}")
            if len(features) > 10:
                print(f"   ... and {len(features) - 10} more")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error updating description: {e}")

if __name__ == '__main__':
    update_enterprise_description()
