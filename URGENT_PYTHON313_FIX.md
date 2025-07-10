# URGENT: Python 3.13 Deployment Fix for Render.com

## Problem
Render.com is using Python 3.13.4 instead of the specified Python 3.11.9, causing build failures with greenlet and other packages.

## Root Cause
- Python 3.13 has breaking changes that affect compiled packages like greenlet (used by SQLAlchemy)
- Our `runtime.txt` file specifying Python 3.11.9 is being ignored

## IMMEDIATE SOLUTION STEPS

### Step 1: Manual Render Configuration
1. Go to your Render dashboard
2. Select your ChamaLink service
3. Go to "Settings" tab
4. Find "Environment" section
5. **MANUALLY SET** these environment variables:
   ```
   PYTHON_VERSION=3.11.9
   RENDER_PYTHON_VERSION=3.11.9
   ```

### Step 2: Update Build Command
In Render dashboard, change the build command to:
```bash
pip install -r requirements-python311.txt
```

### Step 3: Force Redeploy
1. In Render dashboard, go to "Manual Deploy"
2. Click "Clear build cache"
3. Click "Deploy latest commit"

### Step 4: Alternative - Use Docker Deploy
If the above doesn't work, we need to switch to Docker deployment:

1. In Render dashboard, change service type to "Docker"
2. Use this Dockerfile (create it in the repo):

```dockerfile
FROM python:3.11.9-slim

WORKDIR /app
COPY requirements-python311.txt .
RUN pip install -r requirements-python311.txt
COPY . .

EXPOSE 5000
CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:5000"]
```

## Files Added for This Fix
- `requirements-python311.txt` - Python 3.11 specific requirements
- `render.yaml` - Explicit service configuration
- `build.sh` - Build script with Python version checking
- `.python-version` - Python version specification

## What You Need to Do NOW
1. **Go to Render dashboard immediately**
2. **Manually set PYTHON_VERSION=3.11.9 in environment variables**
3. **Clear build cache and redeploy**
4. **If that fails, switch to Docker deployment**

## Verification
After successful deployment, the service should show:
- Python version: 3.11.9
- All packages installed without errors
- Application accessible at your Render URL

## Contact Support
If manual configuration doesn't work, contact Render support and tell them:
"Please configure my service to use Python 3.11.9 exactly. Python 3.13 is breaking my application dependencies."
