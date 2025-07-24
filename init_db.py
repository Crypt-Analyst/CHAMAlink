#!/usr/bin/env python3
"""
Database initialization script for CHAMAlink
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db

def init_database():
    print("🔧 Initializing CHAMAlink Database")
    print("=" * 40)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Drop all existing tables (fresh start)
            print("🗑️ Dropping existing tables...")
            db.drop_all()
            
            # Create all tables from models
            print("🏗️ Creating all tables...")
            db.create_all()
            
            # Verify tables were created
            print("\n📋 Tables created:")
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            for table in sorted(tables):
                print(f"  ✅ {table}")
            
            print(f"\n🎉 Database initialized successfully!")
            print(f"📊 Total tables: {len(tables)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = init_database()
    if success:
        print("\n✅ Database is ready for use!")
    else:
        print("\n❌ Database initialization failed!")
        sys.exit(1)
