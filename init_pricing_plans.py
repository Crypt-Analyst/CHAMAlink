#!/usr/bin/env python3
"""
Initialize subscription plans with multi-month pricing options
"""

from app import create_app, db
from app.models.subscription import SubscriptionPlan, SubscriptionPlanPricing

def initialize_pricing_plans():
    app = create_app()
    with app.app_context():
        # Create/update subscription plans
        plans_data = [
            {
                'name': 'basic',
                'price': 200.0,
                'max_chamas': 1,
                'features': {
                    'basic_reporting': True,
                    'mpesa_integration': True,
                    'member_management': True,
                    'meetings': True,
                    'notifications': True,
                    'export_reports': False,
                    'advanced_analytics': False,
                    'api_access': False,
                    'priority_support': False
                },
                'description': 'Perfect for small chamas'
            },
            {
                'name': 'classic',
                'price': 250.0,
                'max_chamas': 1,
                'features': {
                    'basic_reporting': True,
                    'mpesa_integration': True,
                    'member_management': True,
                    'meetings': True,
                    'notifications': True,
                    'export_reports': True,
                    'advanced_analytics': False,
                    'api_access': False,
                    'priority_support': True
                },
                'description': 'Enhanced features for growing chamas'
            },
            {
                'name': 'basic_plus',
                'price': 350.0,
                'max_chamas': 2,
                'features': {
                    'basic_reporting': True,
                    'mpesa_integration': True,
                    'member_management': True,
                    'meetings': True,
                    'notifications': True,
                    'export_reports': True,
                    'advanced_analytics': True,
                    'api_access': False,
                    'priority_support': True
                },
                'description': 'Advanced features for multiple chamas'
            },
            {
                'name': 'advanced',
                'price': 500.0,
                'max_chamas': -1,  # Unlimited
                'features': {
                    'basic_reporting': True,
                    'mpesa_integration': True,
                    'member_management': True,
                    'meetings': True,
                    'notifications': True,
                    'export_reports': True,
                    'advanced_analytics': True,
                    'api_access': True,
                    'priority_support': True,
                    'white_label': True,
                    'custom_integrations': True
                },
                'description': 'Complete solution for multiple chamas'
            }
        ]
        
        # Create or update plans
        for plan_data in plans_data:
            plan = SubscriptionPlan.query.filter_by(name=plan_data['name']).first()
            if not plan:
                plan = SubscriptionPlan(**plan_data)
                db.session.add(plan)
                print(f"✅ Created plan: {plan_data['name']}")
            else:
                for key, value in plan_data.items():
                    setattr(plan, key, value)
                print(f"✅ Updated plan: {plan_data['name']}")
        
        db.session.commit()
        
        # Create pricing options for each plan
        plans = SubscriptionPlan.query.all()
        
        for plan in plans:
            print(f"\n📋 Setting up pricing for {plan.name} plan (KES {plan.price}/month)")
            
            # Define pricing tiers
            pricing_options = [
                # 1 month - regular price
                {
                    'months': 1,
                    'total_price': plan.price,
                    'bonus_months': 0,
                    'discount_percentage': 0.0
                },
                # 3 months - 5% discount
                {
                    'months': 3,
                    'total_price': plan.price * 3 * 0.95,  # 5% discount
                    'bonus_months': 0,
                    'discount_percentage': 5.0
                },
                # 6 months - 1 free month (equivalent to ~14% discount)
                {
                    'months': 6,
                    'total_price': plan.price * 6,
                    'bonus_months': 1,
                    'discount_percentage': 14.3
                },
                # 12 months - 2 free months (equivalent to ~14% discount)
                {
                    'months': 12,
                    'total_price': plan.price * 12,
                    'bonus_months': 2,
                    'discount_percentage': 14.3
                }
            ]
            
            for option in pricing_options:
                existing = SubscriptionPlanPricing.query.filter_by(
                    plan_id=plan.id, 
                    months=option['months']
                ).first()
                
                if not existing:
                    pricing = SubscriptionPlanPricing(
                        plan_id=plan.id,
                        months=option['months'],
                        price_per_month=option['total_price'] / option['months'],
                        total_price=option['total_price'],
                        bonus_months=option['bonus_months'],
                        discount_percentage=option['discount_percentage']
                    )
                    db.session.add(pricing)
                    
                    bonus_text = f" + {option['bonus_months']} free" if option['bonus_months'] > 0 else ""
                    discount_text = f" ({option['discount_percentage']}% off)" if option['discount_percentage'] > 0 else ""
                    
                    print(f"  💰 {option['months']} months{bonus_text}: KES {option['total_price']:.0f}{discount_text}")
                else:
                    # Update existing pricing
                    existing.price_per_month = option['total_price'] / option['months']
                    existing.total_price = option['total_price']
                    existing.bonus_months = option['bonus_months']
                    existing.discount_percentage = option['discount_percentage']
                    print(f"  ✏️  Updated {option['months']} months pricing")
        
        db.session.commit()
        print(f"\n🎉 All pricing plans initialized successfully!")
        
        # Show summary
        print(f"\n📊 Summary:")
        for plan in plans:
            pricing_count = len(plan.pricing_options)
            print(f"  {plan.name.title()}: {pricing_count} pricing options")

if __name__ == '__main__':
    initialize_pricing_plans()
