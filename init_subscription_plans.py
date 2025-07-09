"""
Initialize subscription plans in the database
"""
from app import create_app, db
from app.models.subscription import SubscriptionPlan

def init_subscription_plans():
    app = create_app()
    
    with app.app_context():
        # Check if plans already exist
        if SubscriptionPlan.query.first():
            print("Subscription plans already exist.")
            return
        
        # Create Basic plan (KES 500)
        basic_plan = SubscriptionPlan(
            name='basic',
            price=500.0,
            max_chamas=1,
            features={
                'loan_management': True,
                'penalty_system': True,
                'notification_system': True,
                'member_management': True,
                'advanced_analytics': False,
                'export_reports': False
            },
            description='Perfect for single chama management with essential features'
        )
        
        # Create Advanced plan (KES 1800)
        advanced_plan = SubscriptionPlan(
            name='advanced',
            price=1800.0,
            max_chamas=999,  # Unlimited
            features={
                'loan_management': True,
                'penalty_system': True,
                'notification_system': True,
                'member_management': True,
                'advanced_analytics': True,
                'export_reports': True,
                'multi_chama': True,
                'priority_support': True
            },
            description='Complete multi-chama management with all premium features'
        )
        
        # Add plans to database
        db.session.add(basic_plan)
        db.session.add(advanced_plan)
        db.session.commit()
        
        print("Subscription plans initialized successfully:")
        print(f"- Basic: KES {basic_plan.price} (1 chama)")
        print(f"- Advanced: KES {advanced_plan.price} (unlimited chamas)")

if __name__ == '__main__':
    init_subscription_plans()
