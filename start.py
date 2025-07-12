#!/usr/bin/env python3
"""
🚀 ChamaLink - Start Application
Clean and ready to run!
"""

print("🧹 CLEANUP COMPLETED!")
print("=" * 50)
print("✅ Deleted all unnecessary documentation files")
print("✅ Removed all test files")
print("✅ Cleaned up duplicate files")
print("✅ Fixed duplicate username display")
print("✅ Added auto-logout (5 minutes)")
print("✅ Role-based system ready")
print("")

# Check user and start app
try:
    from app import create_app
    from app.models.user import User
    
    app = create_app()
    
    with app.app_context():
        test_user = User.query.filter_by(email='masindedoreen762@gmail.com').first()
        if test_user:
            print(f"✅ Test user ready: {test_user.username}")
        else:
            print("ℹ Test user will be created on first run")
    
    print("\n🚀 Starting ChamaLink...")
    print("🌐 URL: http://localhost:5000")
    print("📧 Login: masindedoreen762@gmail.com")
    print("🔑 Password: Masinde762")
    print("=" * 50)
    
    # Start the application
    app.run(debug=True, host='0.0.0.0', port=5000)
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nTry running: C:/Users/bilfo/chamalink/venv/Scripts/python.exe run.py")
