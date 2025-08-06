#!/bin/bash

# QuickBooks Integration Setup Script for CHAMAlink
echo "🎯 CHAMAlink QuickBooks Integration Setup"
echo "========================================"

# Install required packages
echo "📦 Installing QuickBooks integration packages..."
pip install intuit-oauth==1.2.4 python-quickbooks==0.9.5 requests-oauthlib==1.3.1

# Create environment variables template
echo "📝 Creating environment variables template..."
cat > .env.quickbooks << EOF
# QuickBooks Integration Environment Variables
# Get these from https://developer.intuit.com

# QuickBooks App Credentials (from Intuit Developer Dashboard)
QUICKBOOKS_CLIENT_ID=your_client_id_here
QUICKBOOKS_CLIENT_SECRET=your_client_secret_here

# Environment (sandbox for testing, production for live)
QUICKBOOKS_ENVIRONMENT=sandbox

# Redirect URI (must match what's set in Intuit Developer Console)
QUICKBOOKS_REDIRECT_URI=http://localhost:5000/integrations/accounting/quickbooks/callback

# QuickBooks API Base URL
QUICKBOOKS_BASE_URL=https://sandbox-quickbooks.api.intuit.com
EOF

echo "✅ Setup complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Sign up at https://developer.intuit.com"
echo "2. Create a new QuickBooks app"
echo "3. Update the values in .env.quickbooks"
echo "4. Add those variables to your main .env file"
echo "5. Restart your CHAMAlink application"
echo ""
echo "🎉 Then go to /integrations and connect to QuickBooks!"
