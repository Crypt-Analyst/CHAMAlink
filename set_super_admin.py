from app import create_app, db
from app.models.user import User

app = create_app()
with app.app_context():
    # Find Bilford's user
    user = User.query.filter_by(email='bilfordderick@gmail.com').first()
    
    if user:
        print(f"Found user: {user.email}")
        
        # Make sure Bilford is super admin
        user.is_super_admin = True
        user.role = 'super_admin'
        
        db.session.commit()
        
        print("✅ Bilford Bwire set as permanent super admin")
        print(f"  Super Admin: {user.is_super_admin}")
        print(f"  Role: {user.role}")
        print("  ⚡ You now have unlimited access without subscription requirements!")
        
    else:
        print("❌ User not found")
