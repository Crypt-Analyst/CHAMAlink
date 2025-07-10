#!/bin/bash
# Build script for Render.com - Forces Python 3.11

echo "==> ChamaLink Deployment Build Script"
echo "==> Checking Python version..."
python3 --version

# Check if we're using Python 3.13 (not supported)
if python3 --version | grep -q "3.13"; then
    echo "ERROR: Python 3.13 detected - this is not supported!"
    echo "ERROR: ChamaLink requires Python 3.11.x for compatibility"
    echo "ERROR: Please configure your Render service to use Python 3.11.9"
    exit 1
fi

# Check if we're using Python 3.11 (preferred)
if python3 --version | grep -q "3.11"; then
    echo "SUCCESS: Python 3.11 detected - proceeding with build"
else
    echo "WARNING: Python version is not 3.11 - this may cause compatibility issues"
fi

echo "==> Installing dependencies..."
pip install -r requirements.txt

# Optionally install SMS service if needed
if [ "$ENABLE_SMS_SERVICE" = "true" ] || [ -n "$AFRICASTALKING_API_KEY" ]; then
    echo "==> Installing optional SMS service dependencies..."
    pip install africastalking==1.2.5
fi

echo "==> Build completed successfully!"
