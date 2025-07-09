from app import create_app, db
from app.models.subscription import SubscriptionPlan, SubscriptionPlanPricing

app = create_app()
with app.app_context():
    plans = SubscriptionPlan.query.all()
    
    for plan in plans:
        print(f"Setting up pricing for {plan.name} - KES {plan.price}/month")
        
        # Check if pricing already exists
        existing_pricing = SubscriptionPlanPricing.query.filter_by(plan_id=plan.id).first()
        if existing_pricing:
            print(f"  Pricing already exists for {plan.name}")
            continue
        
        # Create pricing options
        pricing_options = [
            # 1 month
            SubscriptionPlanPricing(
                plan_id=plan.id,
                months=1,
                price_per_month=plan.price,
                total_price=plan.price,
                bonus_months=0,
                discount_percentage=0.0
            ),
            # 3 months - 5% discount
            SubscriptionPlanPricing(
                plan_id=plan.id,
                months=3,
                price_per_month=plan.price * 0.95,
                total_price=plan.price * 3 * 0.95,
                bonus_months=0,
                discount_percentage=5.0
            ),
            # 6 months - 1 free month
            SubscriptionPlanPricing(
                plan_id=plan.id,
                months=6,
                price_per_month=plan.price,
                total_price=plan.price * 6,
                bonus_months=1,
                discount_percentage=14.3
            ),
            # 12 months - 2 free months
            SubscriptionPlanPricing(
                plan_id=plan.id,
                months=12,
                price_per_month=plan.price,
                total_price=plan.price * 12,
                bonus_months=2,
                discount_percentage=14.3
            )
        ]
        
        for pricing in pricing_options:
            db.session.add(pricing)
            bonus_text = f" + {pricing.bonus_months} free" if pricing.bonus_months > 0 else ""
            print(f"  {pricing.months} months{bonus_text}: KES {pricing.total_price:.0f}")
        
    db.session.commit()
    print("✅ All pricing options created!")
