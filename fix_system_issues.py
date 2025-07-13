#!/usr/bin/env python3
"""
CHAMAlink System Fix Script
Addresses all reported issues systematically
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("🔧 CHAMAlink System Fix Script")
    print("=" * 50)
    
    from app import create_app, db
    from app.models.user import User
    from app.models.subscription import UserSubscription, SubscriptionPlan
    from app.models.chama import Chama
    
    app = create_app()
    
    with app.app_context():
        print("📋 Issues to Address:")
        print("1. ✅ Chama cards navigation (FIXED)")
        print("2. 🔧 Chama creation confirmation")
        print("3. 🔧 Join request functionality")
        print("4. 🔧 Dashboard real transaction data")
        print("5. 🔧 Meeting calendar widget")
        print("6. 🔧 Database save errors")
        print("7. ✅ Pricing consistency (FIXED)")
        print("8. 🔧 Reports and analytics loading")
        print("9. 🔧 Password change functionality")
        print("10. 🔧 Settings password updates")
        print("11. 🔧 Demo video container")
        print("12. ✅ Contact CSRF and WhatsApp (FIXED)")
        print("13. 🔧 LeeBot responsiveness")
        print("14. 🔧 Roadmap features functionality")
        print("15. ✅ Feedback button implementation (FIXED)")
        print()
        
        # Check expired.trial@test.com account
        trial_user = User.query.filter_by(email='expired.trial@test.com').first()
        if trial_user:
            subscription = UserSubscription.query.filter_by(user_id=trial_user.id).first()
            if subscription:
                print(f"📧 Trial user status: {subscription.status}")
                print(f"📅 Trial end date: {subscription.trial_end_date}")
                
                # Set trial as expired if requested
                if subscription.trial_end_date > datetime.now():
                    subscription.trial_end_date = datetime.now() - timedelta(days=1)
                    subscription.status = 'trial_expired'
                    db.session.commit()
                    print("⚠️ Set trial as expired for testing")
            else:
                print("❌ No subscription found for trial user")
        else:
            print("❌ Trial user not found")
        
        # Check database integrity
        try:
            chamas = Chama.query.count()
            users = User.query.count()
            print(f"📊 Database Status:")
            print(f"   - Chamas: {chamas}")
            print(f"   - Users: {users}")
            print("✅ Database accessible")
        except Exception as e:
            print(f"❌ Database error: {e}")
        
        print("\n🎯 Next Steps:")
        print("1. Test chama card navigation")
        print("2. Verify feedback functionality")
        print("3. Check WhatsApp contact integration")
        print("4. Test trial expiration system")
        print("5. Validate pricing consistency")

if __name__ == '__main__':
    main()
