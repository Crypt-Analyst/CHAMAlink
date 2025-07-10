#!/usr/bin/env python3
"""
Add SACCO_NGO to the existing plantype enum
"""
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db

def add_sacco_ngo_enum():
    """Add SACCO_NGO to the plantype enum"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if SACCO_NGO already exists
            with db.engine.connect() as conn:
                result = conn.execute(db.text("SELECT enumlabel FROM pg_enum WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'plantype')"))
                existing_values = [row[0] for row in result]
                
                if 'SACCO_NGO' not in existing_values:
                    print("Adding SACCO_NGO to plantype enum...")
                    conn.execute(db.text("ALTER TYPE plantype ADD VALUE 'SACCO_NGO'"))
                    conn.commit()
                    print("✅ SACCO_NGO added successfully!")
                else:
                    print("✅ SACCO_NGO already exists in plantype enum")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    add_sacco_ngo_enum()
