# RENDER DEPLOYMENT TROUBLESHOOTING GUIDE

## Current Issue: Greenlet Compilation Error with Python 3.13

### Problem
Render.com is trying to use Python 3.13 instead of the specified Python 3.11.9, causing greenlet (SQLAlchemy dependency) compilation failures.

### Error Symptoms
```
error: '_PyCFrame' does not name a type
ERROR: Failed building wheel for greenlet
```

### Solution Steps

#### 1. Verify Files in Repository
Ensure these files are committed and pushed:
- `runtime.txt` (contains: python-3.11.9)
- `.python-version` (contains: 3.11.9)
- `Procfile` (contains: web: gunicorn run:app --bind 0.0.0.0:$PORT)
- `requirements.txt` (updated with gunicorn==21.2.0)

#### 2. Render.com Service Configuration
1. Go to your Render.com dashboard
2. Select your web service
3. Go to "Settings" tab
4. Under "Build & Deploy":
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn run:app --bind 0.0.0.0:$PORT` (or leave empty if using Procfile)

#### 3. Environment Variables on Render
Copy from `.env.render` file and set these in Render.com:
- PYTHON_VERSION=3.11.9
- FLASK_APP=run.py
- FLASK_ENV=production
- DATABASE_URL=(your Render PostgreSQL URL)
- SECRET_KEY=(generate a secure key)
- All email configuration variables
- Set DEBUG=false

#### 4. Force Python Version
In Render.com Settings:
1. Go to "Environment" section
2. Add environment variable: `PYTHON_VERSION` = `3.11.9`
3. Trigger manual deploy

#### 5. Alternative: Use Different Requirements File
If issues persist, you can:
1. Rename `requirements-production.txt` to `requirements.txt`
2. This file is specifically curated for Python 3.11 compatibility

#### 6. Manual Deploy Trigger
After making changes:
1. Push all changes to GitHub
2. In Render.com dashboard, click "Manual Deploy" → "Deploy latest commit"

### Verification
Once deployed successfully, test:
1. Visit your app URL
2. Check logs for any startup errors
3. Test registration/login functionality
4. Verify email sending works

### Fallback Option
If Python 3.11 still causes issues on Render:
1. Update `runtime.txt` to `python-3.10.12`
2. Update `.python-version` to `3.10.12`
3. All our dependencies are compatible with Python 3.10

### Contact Support
If the issue persists, contact Render support with:
- Link to this troubleshooting guide
- Your service logs
- Mention "Python version override not working"

---
Generated: July 10, 2025
For: ChamaLink Production Deployment
