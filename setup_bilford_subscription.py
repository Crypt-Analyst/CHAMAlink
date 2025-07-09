from app import create_app, db
from app.models.user import User
from app.utils.subscription_utils import ensure_user_has_subscription

app = create_app()
with app.app_context():
    # Find Bilford's user
    user = User.query.filter_by(email='bilfordderick@gmail.com').first()
    
    if user:
        print(f"Found user: {user.email}")
        
        # Ensure user has a subscription
        subscription = ensure_user_has_subscription(user)
        
        print(f"✅ User subscription:")
        print(f"  Plan: {subscription.plan.name}")
        print(f"  Status: {subscription.status}")
        print(f"  Is Active: {subscription.is_active}")
        print(f"  Days Remaining: {subscription.days_remaining}")
        print(f"  Is Trial: {subscription.is_trial}")
        print(f"  Max Chamas: {subscription.plan.max_chamas}")
        
        # Make subscription active (not trial) for testing
        subscription.status = 'active'
        subscription.is_trial = False
        db.session.commit()
        print("✅ Made subscription active (paid) for testing")
        
    else:
        print("❌ User not found")
