"""
Scheduled task to check subscription expiry and send notifications
Run this script daily via cron job
"""
from app import create_app, db
from app.models.subscription import UserSubscription
from app.utils.email_service import send_subscription_email
from datetime import datetime, timedelta

def check_subscription_expiry():
    """Check for subscriptions expiring soon and send notifications"""
    app = create_app()
    
    with app.app_context():
        today = datetime.utcnow()
        seven_days_from_now = today + timedelta(days=7)
        one_day_from_now = today + timedelta(days=1)
        
        # Get subscriptions expiring in 7 days
        subscriptions_7_days = UserSubscription.query.filter(
            UserSubscription.status.in_(['active', 'trial']),
            UserSubscription.end_date.between(seven_days_from_now, seven_days_from_now + timedelta(hours=1))
        ).all()
        
        # Get subscriptions expiring in 1 day
        subscriptions_1_day = UserSubscription.query.filter(
            UserSubscription.status.in_(['active', 'trial']),
            UserSubscription.end_date.between(one_day_from_now, one_day_from_now + timedelta(hours=1))
        ).all()
        
        # Get expired subscriptions (today)
        expired_subscriptions = UserSubscription.query.filter(
            UserSubscription.status.in_(['active', 'trial']),
            UserSubscription.end_date <= today
        ).all()
        
        # Send 7-day expiry warnings
        for subscription in subscriptions_7_days:
            try:
                send_subscription_email(
                    subscription.user.email,
                    'subscription_expiry_warning',
                    {
                        'user': subscription.user,
                        'plan': subscription.plan,
                        'end_date': subscription.end_date,
                        'days_remaining': 7
                    }
                )
                print(f"Sent 7-day expiry warning to {subscription.user.email}")
            except Exception as e:
                print(f"Failed to send 7-day warning to {subscription.user.email}: {e}")
        
        # Send 1-day expiry warnings
        for subscription in subscriptions_1_day:
            try:
                send_subscription_email(
                    subscription.user.email,
                    'subscription_expiry_warning',
                    {
                        'user': subscription.user,
                        'plan': subscription.plan,
                        'end_date': subscription.end_date,
                        'days_remaining': 1
                    }
                )
                print(f"Sent 1-day expiry warning to {subscription.user.email}")
            except Exception as e:
                print(f"Failed to send 1-day warning to {subscription.user.email}: {e}")
        
        # Handle expired subscriptions
        for subscription in expired_subscriptions:
            try:
                # Update subscription status
                subscription.status = 'expired'
                db.session.add(subscription)
                
                # Send expiry notification
                send_subscription_email(
                    subscription.user.email,
                    'subscription_expired',
                    {
                        'user': subscription.user,
                        'plan': subscription.plan,
                        'end_date': subscription.end_date
                    }
                )
                print(f"Sent expiry notification to {subscription.user.email}")
            except Exception as e:
                print(f"Failed to process expired subscription for {subscription.user.email}: {e}")
        
        # Commit all changes
        db.session.commit()
        
        print(f"Processed {len(subscriptions_7_days)} 7-day warnings, "
              f"{len(subscriptions_1_day)} 1-day warnings, "
              f"{len(expired_subscriptions)} expired subscriptions")

if __name__ == '__main__':
    check_subscription_expiry()
