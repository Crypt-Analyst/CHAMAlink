#!/usr/bin/env python3
"""Clean up SACCO/NGO plan from database"""

import os
import sys
from app import create_app, db

def cleanup_sacco_plan():
    """Remove SACCO/NGO plan from database"""
    app = create_app()
    
    with app.app_context():
        print("🧹 Cleaning up SACCO/NGO plan from database...")
        
        # Delete using SQL to avoid enum issues
        try:
            result = db.session.execute(db.text("""
                DELETE FROM enterprise_subscription_plans 
                WHERE plan_type = 'sacco_ngo'
            """))
            
            deleted_count = result.rowcount
            print(f"✅ Deleted {deleted_count} SACCO/NGO plan(s)")
            
            db.session.commit()
            print("✅ Database cleanup completed")
            
            # Verify cleanup
            remaining = db.session.execute(db.text("""
                SELECT count(*) FROM enterprise_subscription_plans 
                WHERE plan_type = 'sacco_ngo'
            """)).scalar()
            
            if remaining == 0:
                print("✅ No SACCO/NGO plans remain in database")
            else:
                print(f"⚠️ {remaining} SACCO/NGO plans still exist")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error during cleanup: {e}")

if __name__ == '__main__':
    cleanup_sacco_plan()
