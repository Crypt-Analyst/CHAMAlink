#!/usr/bin/env python3
"""
Complete diagnosis for ChamaLink 500 error
Run this locally to identify the exact issue
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def diagnose_500_error():
    """Comprehensive diagnosis of the 500 error"""
    print("🔍 CHAMALINK 500 ERROR DIAGNOSIS")
    print("=" * 50)
    
    # 1. Check environment variables
    print("1. 🔧 ENVIRONMENT VARIABLES:")
    print("-" * 30)
    required_vars = ['DATABASE_URL', 'SECRET_KEY', 'FLASK_DEBUG']
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            if 'SECRET' in var or 'PASSWORD' in var:
                print(f"✅ {var}: {'*' * len(value)}")
            elif 'DATABASE_URL' in var:
                print(f"✅ {var}: {value[:20]}...{value[-10:]}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
    
    # 2. Test database connection
    print("\n2. 🗄️  DATABASE CONNECTION:")
    print("-" * 30)
    try:
        from app import create_app, db
        app = create_app()
        
        with app.app_context():
            # Test basic connection
            result = db.engine.execute('SELECT version()')
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL connected: {version[:50]}...")
            
            # Check if tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"✅ Found {len(tables)} tables")
            
            # Check specific tables
            required_tables = ['user', 'enterprise_subscription_plans']
            for table in required_tables:
                if table in tables:
                    print(f"✅ {table} table exists")
                else:
                    print(f"❌ {table} table MISSING")
                    
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    # 3. Test model imports
    print("\n3. 📦 MODEL IMPORTS:")
    print("-" * 30)
    try:
        from app.models.user import User
        from app.models.chama import Chama
        from app.models.enterprise import EnterpriseSubscriptionPlan
        print("✅ All models imported successfully")
        
        # Test model queries
        with app.app_context():
            user_count = User.query.count()
            chama_count = Chama.query.count()
            plan_count = EnterpriseSubscriptionPlan.query.count()
            
            print(f"✅ Users: {user_count}")
            print(f"✅ Chamas: {chama_count}") 
            print(f"✅ Plans: {plan_count}")
            
            if plan_count == 0:
                print("⚠️  No subscription plans found - this could cause errors")
                
    except Exception as e:
        print(f"❌ Model error: {e}")
        return False
    
    # 4. Test form imports
    print("\n4. 📝 FORM IMPORTS:")
    print("-" * 30)
    try:
        from app.auth.forms import LoginForm, RegistrationForm
        
        with app.app_context():
            login_form = LoginForm()
            reg_form = RegistrationForm()
            print("✅ Forms created successfully")
            
    except Exception as e:
        print(f"❌ Form error: {e}")
        return False
    
    # 5. Test route imports
    print("\n5. 🛣️  ROUTE IMPORTS:")
    print("-" * 30)
    try:
        from app.auth.routes import auth
        from app.routes.main import main_blueprint
        print("✅ Core routes imported successfully")
        
    except Exception as e:
        print(f"❌ Route import error: {e}")
        return False
    
    # 6. Test app creation
    print("\n6. 🚀 APP CREATION:")
    print("-" * 30)
    try:
        with app.app_context():
            # Test that we can access the app context
            from flask import current_app
            print(f"✅ App context working: {current_app.name}")
            print(f"✅ Debug mode: {current_app.debug}")
            print(f"✅ Secret key set: {bool(current_app.secret_key)}")
            
    except Exception as e:
        print(f"❌ App context error: {e}")
        return False
    
    print("\n🎯 DIAGNOSIS COMPLETE!")
    print("=" * 50)
    return True

def suggest_fixes():
    """Suggest fixes based on common issues"""
    print("\n💡 SUGGESTED FIXES:")
    print("-" * 20)
    print("1. 🗄️  If database tables are missing:")
    print("   Run: python init_database.py")
    print()
    print("2. 📦 If subscription plans are missing:")
    print("   The init_database.py script will create them")
    print()
    print("3. 🔧 If environment variables are missing:")
    print("   Make sure all variables are set in Render.com dashboard")
    print()
    print("4. 🌐 To check live application:")
    print("   Visit: https://chamalink.onrender.com/health")
    print()
    print("5. 📋 To see detailed error info:")
    print("   Enable debug mode by setting FLASK_DEBUG=true")

if __name__ == "__main__":
    print("Starting ChamaLink diagnosis...")
    
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded .env file")
    except:
        print("⚠️  Could not load .env file")
    
    success = diagnose_500_error()
    suggest_fixes()
    
    if success:
        print("\n🎉 All tests passed! The issue might be environment-specific.")
        print("🔍 Check the live /health endpoint for production-specific issues.")
    else:
        print("\n❌ Found issues that need to be fixed.")
        print("🔧 Follow the suggested fixes above.")
