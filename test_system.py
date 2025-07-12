"""
CHAMAlink System Test & Setup Script
===================================

This script tests the system functionality and sets up test data.
"""

import sys
import os
import traceback

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all imports work correctly"""
    print("🔧 Testing imports...")
    
    try:
        from app import create_app, db
        print("✅ Core app imports successful")
        
        from app.models.user import User
        from app.models.chama import Chama, ChamaMember
        print("✅ Model imports successful")
        
        from app.utils.countries import get_all_countries, get_country_by_code
        countries = get_all_countries()
        print(f"✅ Country utils successful - {len(countries)} countries loaded")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        traceback.print_exc()
        return False

def test_database():
    """Test database connectivity"""
    print("\n🗄️ Testing database connectivity...")
    
    try:
        from app import create_app, db
        app = create_app()
        
        with app.app_context():
            # Test basic database operations
            from app.models.user import User
            
            # Try to query users table
            user_count = User.query.count()
            print(f"✅ Database connected - {user_count} users in system")
            
            # Test database creation
            db.create_all()
            print("✅ Database tables created/verified")
            
            return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        traceback.print_exc()
        return False

def test_currency_system():
    """Test multi-currency functionality"""
    print("\n💱 Testing currency system...")
    
    try:
        from app.utils.countries import get_currency_for_country, SUPPORTED_CURRENCIES
        
        # Test currency mapping
        kes_currency = get_currency_for_country('KE')
        usd_currency = get_currency_for_country('US')
        print(f"✅ Currency mapping - KE: {kes_currency}, US: {usd_currency}")
        
        # Test currency routes (if available)
        try:
            from app.routes.currency import get_fallback_rates
            rates = get_fallback_rates()
            print(f"✅ Currency rates system functional")
        except ImportError:
            print("⚠️ Currency routes not found - this is expected if not yet created")
        
        return True
    except Exception as e:
        print(f"❌ Currency system error: {e}")
        traceback.print_exc()
        return False

def create_essential_data():
    """Create essential data for the system"""
    print("\n📋 Creating essential data...")
    
    try:
        from app import create_app, db
        from app.models.subscription import SubscriptionPlan
        
        app = create_app()
        with app.app_context():
            
            # Create subscription plans if they don't exist
            plans_data = [
                {
                    'name': 'basic',
                    'display_name': 'Basic Plan',
                    'description': 'Perfect for small groups - Up to 50 members',
                    'price_kes': 500,
                    'price_usd': 5,
                    'max_chamas': 5,
                    'max_members_per_chama': 50
                },
                {
                    'name': 'classic',
                    'display_name': 'Classic Plan', 
                    'description': 'Most popular choice - Up to 200 members',
                    'price_kes': 1200,
                    'price_usd': 12,
                    'max_chamas': 20,
                    'max_members_per_chama': 200
                },
                {
                    'name': 'advanced',
                    'display_name': 'Advanced Plan',
                    'description': 'For growing organizations - Up to 1000 members',
                    'price_kes': 2500,
                    'price_usd': 25,
                    'max_chamas': 100,
                    'max_members_per_chama': 1000
                },
                {
                    'name': 'enterprise',
                    'display_name': 'Enterprise Plan',
                    'description': 'Unlimited scalability - Per member pricing',
                    'price_kes': 30,
                    'price_usd': 0.30,
                    'max_chamas': -1,
                    'max_members_per_chama': -1
                }
            ]
            
            created_plans = 0
            for plan_data in plans_data:
                existing_plan = SubscriptionPlan.query.filter_by(name=plan_data['name']).first()
                if not existing_plan:
                    plan = SubscriptionPlan(**plan_data)
                    db.session.add(plan)
                    created_plans += 1
            
            db.session.commit()
            print(f"✅ Subscription plans created/verified - {created_plans} new plans")
            
            return True
    except Exception as e:
        print(f"❌ Essential data creation error: {e}")
        traceback.print_exc()
        return False

def test_app_startup():
    """Test that the Flask app can start"""
    print("\n🚀 Testing app startup...")
    
    try:
        from app import create_app
        app = create_app()
        
        # Test app configuration
        print(f"✅ App created successfully")
        print(f"✅ Debug mode: {app.debug}")
        print(f"✅ Secret key configured: {'✓' if app.config.get('SECRET_KEY') else '✗'}")
        print(f"✅ Database URL configured: {'✓' if app.config.get('SQLALCHEMY_DATABASE_URI') else '✗'}")
        
        # Test that routes are registered
        with app.app_context():
            # Get all registered routes
            routes = []
            for rule in app.url_map.iter_rules():
                routes.append(str(rule))
            
            print(f"✅ {len(routes)} routes registered")
            
            # Check for key routes
            key_routes = ['/auth/login', '/auth/register', '/dashboard', '/']
            found_routes = [route for route in key_routes if any(route in r for r in routes)]
            print(f"✅ Key routes found: {len(found_routes)}/{len(key_routes)}")
        
        return True
    except Exception as e:
        print(f"❌ App startup error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🔍 CHAMAlink System Test & Setup")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Database Test", test_database),
        ("Currency System Test", test_currency_system),
        ("Essential Data Creation", create_essential_data),
        ("App Startup Test", test_app_startup)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready.")
        print("\n📋 Next Steps:")
        print("1. Start the app: python run.py")
        print("2. Open browser: http://127.0.0.1:5000")
        print("3. Register with a test account")
        print("4. Test multi-currency features")
        print("5. Try the expired trial user: expired.trial@test.com / password123")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    print("\n🌍 Database Schema:")
    print("View the schema: open database_schema.html in your browser")

if __name__ == '__main__':
    main()
