#!/usr/bin/env python3
"""Test script to check if template formatting issues are fixed"""

import os
import sys
from app import create_app, db
from app.models.enterprise import EnterpriseSubscriptionPlan

def test_template_rendering():
    """Test template rendering with actual data"""
    app = create_app()
    
    with app.app_context():
        # Get plans from database
        plans = EnterpriseSubscriptionPlan.query.filter_by(is_active=True).all()
        
        print(f"Found {len(plans)} active plans")
        
        for plan in plans:
            print(f"\nPlan: {plan.name}")
            print(f"  max_members_per_chama: {plan.max_members_per_chama}")
            print(f"  price_monthly: {plan.price_monthly}")
            print(f"  Type of max_members_per_chama: {type(plan.max_members_per_chama)}")
            print(f"  Type of price_monthly: {type(plan.price_monthly)}")
            
            # Test string formatting
            try:
                if plan.max_members_per_chama is not None:
                    formatted = "{:,}".format(plan.max_members_per_chama)
                    print(f"  Formatted max_members: {formatted}")
                else:
                    print(f"  max_members_per_chama is None")
                    
                if plan.price_monthly is not None:
                    formatted = "{:,.0f}".format(plan.price_monthly)
                    print(f"  Formatted price: {formatted}")
                else:
                    print(f"  price_monthly is None")
                    
            except Exception as e:
                print(f"  ERROR formatting: {e}")

if __name__ == '__main__':
    test_template_rendering()
