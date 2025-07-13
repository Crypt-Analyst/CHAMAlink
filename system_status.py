"""
CHAMAlink System Status Check
============================
Checks database, git, and overall system status
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_database_status():
    """Check database connectivity and structure"""
    print("🗄️ CHECKING DATABASE STATUS")
    print("-" * 40)
    
    try:
        from app import create_app, db
        from app.models.user import User
        from app.models.chama import Chama
        from app.models.subscription import SubscriptionPlan
        
        app = create_app()
        with app.app_context():
            # Test database connection
            try:
                user_count = User.query.count()
                chama_count = Chama.query.count()
                plan_count = SubscriptionPlan.query.count()
                
                print(f"✅ Database connected successfully")
                print(f"✅ Users in system: {user_count}")
                print(f"✅ Chamas in system: {chama_count}")
                print(f"✅ Subscription plans: {plan_count}")
                
                # Check if new fields exist
                try:
                    # Test new currency and country fields
                    test_user = User.query.first()
                    if test_user:
                        currency = getattr(test_user, 'preferred_currency', None)
                        country = getattr(test_user, 'country_code', None)
                        print(f"✅ Multi-currency fields: {'✓' if currency is not None else '✗'}")
                        print(f"✅ Country fields: {'✓' if country is not None else '✗'}")
                    else:
                        print("⚠️ No users in database - creating test user...")
                        return create_test_user()
                        
                except Exception as e:
                    print(f"⚠️ New fields not fully available: {e}")
                    print("ℹ️ Running db.create_all() to ensure all tables exist...")
                    db.create_all()
                    print("✅ Database tables created/updated")
                
                return True
                
            except Exception as e:
                print(f"❌ Database connection error: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def create_test_user():
    """Create a test user to verify database functionality"""
    try:
        from app import create_app, db
        from app.models.user import User
        from werkzeug.security import generate_password_hash
        from datetime import timedelta
        
        app = create_app()
        with app.app_context():
            db.create_all()
            
            # Check if test user exists
            test_user = User.query.filter_by(email='expired.trial@test.com').first()
            if test_user:
                print("✅ Test user already exists")
                return True
            
            # Create test user with new fields
            test_user = User(
                username='expired_trial',
                email='expired.trial@test.com',
                phone_number='+254701234567',
                password_hash=generate_password_hash('password123'),
                first_name='Trial',
                last_name='Expired',
                is_email_verified=True,
                created_at=datetime.now() - timedelta(days=20)
            )
            
            # Add new fields if they exist
            if hasattr(test_user, 'country_code'):
                test_user.country_code = 'KE'
                test_user.country_name = 'Kenya'
            
            if hasattr(test_user, 'preferred_currency'):
                test_user.preferred_currency = 'KES'
            
            db.session.add(test_user)
            db.session.commit()
            
            print("✅ Test user created successfully")
            print("   Email: expired.trial@test.com")
            print("   Password: password123")
            
            return True
            
    except Exception as e:
        print(f"❌ Test user creation failed: {e}")
        return False

def check_git_status():
    """Check git repository status"""
    print("\n📁 CHECKING GIT STATUS")
    print("-" * 40)
    
    try:
        import subprocess
        
        # Check if we're in a git repo
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            if result.stdout.strip():
                print("⚠️ Uncommitted changes found:")
                print(result.stdout)
                print("ℹ️ Run 'git add . && git commit -m \"message\"' to commit")
            else:
                print("✅ Working directory clean - all changes committed")
            
            # Check remote status
            try:
                remote_result = subprocess.run(['git', 'status', '-uno'], 
                                             capture_output=True, text=True, cwd=os.getcwd())
                if 'ahead' in remote_result.stdout:
                    print("⚠️ Local commits not pushed to remote")
                    print("ℹ️ Run 'git push origin master' to push changes")
                elif 'behind' in remote_result.stdout:
                    print("⚠️ Remote has changes not pulled locally")
                    print("ℹ️ Run 'git pull origin master' to get latest changes")
                else:
                    print("✅ Local and remote repositories are synchronized")
                    
            except Exception as e:
                print(f"ℹ️ Could not check remote status: {e}")
            
            return True
            
        else:
            print(f"❌ Git error: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ Git not found - please install Git")
        return False
    except Exception as e:
        print(f"❌ Git check failed: {e}")
        return False

def check_app_status():
    """Check if the Flask app is running properly"""
    print("\n🚀 CHECKING APPLICATION STATUS")
    print("-" * 40)
    
    try:
        from app import create_app
        
        app = create_app()
        print("✅ Flask app creates successfully")
        print(f"✅ Debug mode: {app.debug}")
        print(f"✅ Secret key configured: {'✓' if app.config.get('SECRET_KEY') else '✗'}")
        print(f"✅ Database URL: {'✓' if app.config.get('SQLALCHEMY_DATABASE_URI') else '✗'}")
        
        # Check blueprints
        blueprints = list(app.blueprints.keys())
        print(f"✅ Registered blueprints: {len(blueprints)}")
        
        # Check for key blueprints
        key_blueprints = ['auth', 'main', 'chama', 'currency']
        found_blueprints = [bp for bp in key_blueprints if bp in blueprints]
        print(f"✅ Key blueprints: {len(found_blueprints)}/{len(key_blueprints)} found")
        
        if 'currency' in blueprints:
            print("✅ Multi-currency system is registered")
        else:
            print("⚠️ Currency system not registered")
        
        return True
        
    except Exception as e:
        print(f"❌ App check failed: {e}")
        return False

def main():
    """Run all status checks"""
    print("🔍 CHAMAlink System Status Check")
    print("=" * 50)
    print(f"📅 Check performed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    checks = [
        ("Database", check_database_status),
        ("Git Repository", check_git_status),
        ("Application", check_app_status)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} check crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("-" * 20)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")
    
    print(f"\nOverall Status: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 System is fully operational!")
        print("\n📋 Next Steps:")
        print("1. Start the app: python run.py")
        print("2. Open browser: http://127.0.0.1:5000")
        print("3. Test with: expired.trial@test.com / password123")
    else:
        print("\n⚠️ Some issues found - please address them above")
    
    print(f"\n🌍 Database Schema: Open 'database_schema.html' to view")
    print(f"🔗 GitHub: https://github.com/RahasoftBwire/CHAMAlink")

if __name__ == '__main__':
    main()
