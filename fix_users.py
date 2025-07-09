from app import create_app, db
from app.models.user import User

app = create_app()
with app.app_context():
    users = User.query.all()
    for user in users:
        print(f'User: {user.email}, Verified: {user.is_email_verified}')
        if not user.is_email_verified:
            user.is_email_verified = True
            print(f'  ✅ Verified {user.email}')
    
    db.session.commit()
    print('All users are now verified!')
