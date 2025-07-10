#!/usr/bin/env python3
"""Debug pricing page issues"""

from app import create_app, db
from app.models.enterprise import EnterpriseSubscriptionPlan

def debug_pricing():
    """Debug the pricing page template"""
    app = create_app()
    
    with app.app_context():
        plans = EnterpriseSubscriptionPlan.query.filter_by(is_active=True).order_by(EnterpriseSubscriptionPlan.price_monthly).all()
        
        print(f"Found {len(plans)} active plans")
        
        for plan in plans:
            print(f"\nPlan: {plan.name}")
            print(f"  Type: {plan.plan_type.value}")
            print(f"  Price Monthly: {plan.price_monthly}")
            print(f"  Price Yearly: {plan.price_yearly}")
            
            try:
                yearly_savings = plan.get_yearly_savings()
                print(f"  Yearly Savings: {yearly_savings}")
            except Exception as e:
                print(f"  ERROR in get_yearly_savings(): {e}")
                
            try:
                features = plan.get_feature_list()
                print(f"  Features: {len(features)} items")
            except Exception as e:
                print(f"  ERROR in get_feature_list(): {e}")

if __name__ == '__main__':
    debug_pricing()
