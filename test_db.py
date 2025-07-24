from app import create_app
from app.models.user import User
from app.models import db

print("🔍 Testing database connection...")

app = create_app()
with app.app_context():
    try:
        # Test database connection
        user_count = User.query.count()
        print(f"✅ Database connection successful")
        print(f"👤 Users in database: {user_count}")
        
        # Ensure all tables exist
        db.create_all()
        print("✅ All database tables verified")
        
        print("\n🎉 Database is working correctly!")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback
        traceback.print_exc()
