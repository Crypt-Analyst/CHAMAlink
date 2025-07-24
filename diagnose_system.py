#!/usr/bin/env python3
"""
CHAMAlink Database Verification Script
Quick diagnostic to check database status and app functionality
"""

import sys
import os
import sqlite3
import requests
from datetime import datetime

def check_database():
    print("🔍 DATABASE VERIFICATION")
    print("=" * 40)
    
    db_path = "instance/chamalink.db"
    
    # Check if database file exists
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
        
    print(f"✅ Database file exists: {db_path}")
    print(f"📊 File size: {os.path.getsize(db_path)} bytes")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Tables found: {len(tables)}")
        for table in tables:
            print(f"  • {table}")
            
            # Get row count
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"    └─ {count} rows")
            except Exception as e:
                print(f"    └─ Error: {e}")
        
        # Check required tables
        required_tables = ['users', 'chamas', 'alembic_version']
        missing_tables = []
        
        for table in required_tables:
            if table not in tables:
                missing_tables.append(table)
        
        if missing_tables:
            print(f"❌ Missing required tables: {missing_tables}")
            return False
        else:
            print("✅ All required tables present")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_app():
    print("\n🌐 APPLICATION VERIFICATION")
    print("=" * 40)
    
    base_url = "http://127.0.0.1:5000"
    endpoints = [
        "/",
        "/auth/login",
        "/auth/register", 
        "/api/developer",
        "/subscription/upgrade"
    ]
    
    all_working = True
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {endpoint} - Working (Status: {response.status_code})")
            else:
                print(f"❌ {endpoint} - Error (Status: {response.status_code})")
                all_working = False
                
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint} - Connection failed (Flask app not running?)")
            all_working = False
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
            all_working = False
    
    return all_working

def check_flask_models():
    print("\n🏗️ FLASK MODELS VERIFICATION")
    print("=" * 40)
    
    try:
        # Import Flask app and models
        sys.path.append('.')
        from app import create_app
        from app.models.user import User
        from app.models import db
        
        app = create_app()
        
        with app.app_context():
            # Test database connection through Flask
            user_count = User.query.count()
            print(f"✅ Flask-SQLAlchemy connection working")
            print(f"👤 Users in database: {user_count}")
            
            # Test if we can create tables (safe operation)
            db.create_all()
            print("✅ Database tables verified/created")
            
        return True
        
    except Exception as e:
        print(f"❌ Flask models error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print(f"🔍 CHAMAlink System Diagnostic")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Check database
    db_ok = check_database()
    
    # Check Flask models
    models_ok = check_flask_models()
    
    # Check web app
    app_ok = check_app()
    
    # Final summary
    print("\n" + "=" * 50)
    print("🏆 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    print(f"Database Status: {'✅ OK' if db_ok else '❌ FAILED'}")
    print(f"Flask Models: {'✅ OK' if models_ok else '❌ FAILED'}")
    print(f"Web Application: {'✅ OK' if app_ok else '❌ FAILED'}")
    
    if db_ok and models_ok and app_ok:
        print("\n🎉 All systems operational!")
        print("✅ CHAMAlink is ready to use")
    else:
        print("\n⚠️ Some issues detected")
        print("❌ Check the details above for troubleshooting")

if __name__ == "__main__":
    main()
