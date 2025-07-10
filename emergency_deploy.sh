#!/bin/bash
# Emergency deployment script for ChamaLink
# Use this if normal deployment fails due to dependency issues

echo "🚨 ChamaLink Emergency Deployment Script"
echo "=" * 50

echo "🔍 Checking Python version..."
python3 --version

echo "📦 Attempting installation with minimal requirements..."

# Try minimal requirements first
if pip install -r requirements-minimal.txt; then
    echo "✅ Minimal requirements installed successfully"
    
    echo "📦 Installing optional packages individually..."
    
    # Try to install optional packages one by one
    optional_packages=(
        "reportlab==4.0.4"
        "python-dateutil==2.8.2"
        "africastalking==1.2.5"
        "qrcode==7.4.2"
        "Pillow==9.5.0"
        "colorama==0.4.6"
    )
    
    for package in "${optional_packages[@]}"; do
        echo "📦 Installing $package..."
        if pip install "$package"; then
            echo "✅ $package installed successfully"
        else
            echo "⚠️  $package failed to install (will use fallback)"
        fi
    done
    
    echo "✅ Emergency deployment completed"
    echo "🔧 Application will use fallback implementations for missing packages"
    
else
    echo "❌ Even minimal requirements failed to install"
    echo "🔧 Check Python version and network connectivity"
    exit 1
fi
