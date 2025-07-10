# ChamaLink Deployment Guide - Render.com

## Quick Deployment Steps

### 1. Repository Setup
- ✅ Repository is already connected to Render.com
- ✅ Latest code has been pushed to GitHub

### 2. Environment Variables Setup
In your Render.com dashboard, add these environment variables:

```
DATABASE_URL=your_supabase_or_postgres_url
SECRET_KEY=your_secure_secret_key
FLASK_ENV=production
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_gmail@gmail.com
MAIL_PASSWORD=your_gmail_app_password
MAIL_DEFAULT_SENDER=your_gmail@gmail.com
```

### 3. Build Settings
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn run:app`
- **Environment**: Python 3.11.x (recommended for better package compatibility)

### 4. Database Setup
1. Create a PostgreSQL database on Supabase or Render
2. Update DATABASE_URL environment variable
3. Run database migrations after first deployment

### 5. Email Configuration
1. Enable 2-factor authentication on your Gmail account
2. Generate an app password for ChamaLink
3. Use the app password (not your regular password) in MAIL_PASSWORD

## Environment Variables Required

### Core Application
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Flask secret key for sessions
- `FLASK_ENV` - Set to 'production'

### Email System
- `MAIL_SERVER` - smtp.gmail.com
- `MAIL_PORT` - 587
- `MAIL_USE_TLS` - True
- `MAIL_USERNAME` - Your Gmail address
- `MAIL_PASSWORD` - Gmail app password
- `MAIL_DEFAULT_SENDER` - Your Gmail address

### Optional (for future features)
- `MPESA_CONSUMER_KEY` - M-Pesa API key
- `MPESA_CONSUMER_SECRET` - M-Pesa API secret
- `AFRICASTALKING_USERNAME` - SMS service username
- `AFRICASTALKING_API_KEY` - SMS service API key

## Post-Deployment Steps

### 1. Database Migration
Run these commands in Render.com shell:
```bash
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

### 2. Create Super Admin User
```bash
python -c "
from app import create_app, db
from app.models.user import User
app = create_app()
with app.app_context():
    admin = User(username='admin', email='admin@yourdomain.com', first_name='Admin', last_name='User')
    admin.set_password('your_secure_password')
    admin.is_super_admin = True
    admin.is_email_verified = True
    db.session.add(admin)
    db.session.commit()
    print('Super admin created successfully')
"
```

### 3. Test Core Functionality
- ✅ Homepage loads correctly
- ✅ User registration works
- ✅ Email sending works
- ✅ Login/logout works
- ✅ Dashboard accessible

## Troubleshooting

### Common Issues

#### Build Fails
- Check requirements.txt for correct package versions
- Ensure Python version compatibility (3.11.x recommended)
- Latest fix: Updated Flask-Mail from 0.10.1 to 0.10.0
- Latest fix: Removed problematic packages (pandas, matplotlib) that cause compilation issues

#### Database Connection Fails
- Verify DATABASE_URL is correct
- Ensure database allows connections from Render.com IPs

#### Email Not Sending
- Verify Gmail app password is correct
- Check that 2FA is enabled on Gmail account
- Ensure MAIL_* environment variables are set correctly

## Success Metrics

### Launch Checklist
- ✅ Application deploys successfully
- ✅ All core features work
- ✅ Email system operational
- ✅ Security features active
- ✅ Performance acceptable
- ✅ SSL certificate active
- ✅ Database migrations complete

---

**ChamaLink is ready for production deployment! 🚀**

Last Updated: July 10, 2025
Version: 1.0 Production Ready
