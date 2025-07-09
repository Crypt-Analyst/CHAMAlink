from app import create_app, db
from app.models.user import User
from datetime import date

app = create_app()
with app.app_context():
    # Find user by email
    user = User.query.filter_by(email='bilfordderick@gmail.com').first()
    
    if user:
        print(f"Found user: {user.email}")
        
        # Update user details
        user.first_name = 'Bilford'
        user.last_name = 'Bwire'
        user.phone_number = '0722206805'
        user.national_id = '37763572'
        user.date_of_birth = date(2000, 10, 28)
        
        db.session.commit()
        print("✅ Updated user details:")
        print(f"  Name: {user.first_name} {user.last_name}")
        print(f"  Phone: {user.phone_number}")
        print(f"  ID: {user.national_id}")
        print(f"  DOB: {user.date_of_birth}")
    else:
        print("❌ User not found")
