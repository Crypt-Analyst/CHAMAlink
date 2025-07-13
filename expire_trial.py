"""
Script to expire trial for testing account
"""
from app import create_app, db
from app.models.user import User
from app.models.subscription import UserSubscription, SubscriptionPlan
from datetime import datetime, timedelta

app = create_app()
with app.app_context():
    # Find the test user
    user = User.query.filter_by(email='expired.trial@test.com').first()
    if user:
        print(f'Found user: {user.username}')
        
        # Check current subscription
        subscription = UserSubscription.query.filter_by(user_id=user.id).first()
        if subscription:
            print(f'Current subscription: {subscription.status}, ends: {subscription.end_date}')
            # Expire the trial (set to 35 days ago to simulate expired trial)
            subscription.trial_end_date = datetime.now() - timedelta(days=35)
            subscription.end_date = datetime.now() - timedelta(days=5)
            subscription.status = 'trial_expired'
            subscription.is_trial = True
        else:
            # Create expired trial subscription
            basic_plan = SubscriptionPlan.query.filter_by(name='basic').first()
            if not basic_plan:
                basic_plan = SubscriptionPlan(
                    name='basic',
                    price=200.0,
                    max_chamas=5,
                    features={'max_members_per_chama': 20, 'basic_reports': True},
                    description='Basic plan for small chamas'
                )
                db.session.add(basic_plan)
                db.session.flush()
            
            subscription = UserSubscription(
                user_id=user.id,
                plan_id=basic_plan.id,
                status='trial_expired',
                start_date=datetime.now() - timedelta(days=35),
                end_date=datetime.now() - timedelta(days=5),
                trial_end_date=datetime.now() - timedelta(days=5),
                is_trial=True
            )
            db.session.add(subscription)
        
        db.session.commit()
        print('✅ Trial has been expired for expired.trial@test.com')
        print(f'Trial ended: {subscription.trial_end_date}')
        print(f'Subscription ends: {subscription.end_date}')
    else:
        print('❌ User expired.trial@test.com not found')
