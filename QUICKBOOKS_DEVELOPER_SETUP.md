# 🔗 REAL QUICKBOOKS DEVELOPER SETUP FOR CHAMALINK

## 🎯 Getting Real QuickBooks Developer Credentials

### Step 1: Create Intuit Developer Account

1. **Go to Intuit Developer Portal**
   - Visit: [https://developer.intuit.com](https://developer.intuit.com)
   - Click **"Sign up"** (top right corner)

2. **Create Account**
   - Use your business email address
   - Choose **"QuickBooks Online"** as your primary interest
   - Complete the registration process

3. **Verify Your Account**
   - Check your email for verification link
   - Complete email verification

### Step 2: Create Your CHAMAlink App

1. **Access Developer Dashboard**
   - Login to [https://developer.intuit.com](https://developer.intuit.com)
   - Click **"My Apps"** in the top navigation

2. **Create New App**
   - Click **"Create an app"**
   - Choose **"QuickBooks Online and Payments"**
   
3. **App Configuration**
   ```
   App Name: CHAMAlink QuickBooks Integration
   Description: Professional chama financial management system
   Industry: Financial Services
   App Type: Web Application
   ```

4. **Redirect URIs (IMPORTANT!)**
   Add these exact URLs:
   ```
   Development: http://localhost:5000/integrations/accounting/quickbooks/callback
   Production: https://yourdomain.com/integrations/accounting/quickbooks/callback
   ```

### Step 3: Get Your Credentials

1. **Development Keys**
   - Go to **"Keys & OAuth"** tab in your app
   - Copy **Client ID** (starts with `AB...`)
   - Copy **Client Secret** (longer string)

2. **Sandbox Company**
   - Intuit provides test company data automatically
   - You'll get a "Realm ID" when you connect

### Step 4: Set Up Environment Variables

Create or update your `.env` file:

```env
# QuickBooks Development Credentials
QUICKBOOKS_CLIENT_ID=ABcd1234567890abcdef1234567890ab
QUICKBOOKS_CLIENT_SECRET=your_actual_client_secret_from_intuit_here
QUICKBOOKS_REDIRECT_URI=http://localhost:5000/integrations/accounting/quickbooks/callback
QUICKBOOKS_ENVIRONMENT=sandbox
QUICKBOOKS_BASE_URL=https://sandbox-quickbooks.api.intuit.com

# For Production (when ready)
# QUICKBOOKS_ENVIRONMENT=production  
# QUICKBOOKS_BASE_URL=https://quickbooks.api.intuit.com
```

## 🚀 Testing Your Connection

### Run the Setup Script
```bash
cd /home/bwire/CHAMAlink
./setup_quickbooks.sh
```

### Test Integration
```bash
python test_quickbooks.py
```

### Connect in CHAMAlink
1. Restart your CHAMAlink application
2. Go to: `http://localhost:5000/integrations`
3. Find "QuickBooks Online" section
4. Click **"Connect to QuickBooks"**
5. Authorize with your Intuit account
6. Success! You're connected to sandbox

## 📊 What You'll See in QuickBooks Sandbox

### Test Data Available:
- Sample customers (your chamas will be added here)
- Chart of accounts (new accounts will be created)
- Transaction history
- Financial reports

### CHAMAlink Will Create:
```
Customers:
- Smart Investors Chama
- Unity Savings Group
- Progressive Women Chama

Accounts:
- Member Contributions (Income)
- Chama Expenses (Expense)
- Loans Payable (Liability)
- Cash - Chama Account (Asset)

Transactions:
- Member contributions as journal entries
- Expense payments
- Loan disbursements and repayments
```

## 🔑 Production Deployment

### When Ready for Live Data:

1. **Submit for Review**
   - In developer.intuit.com, submit your app for review
   - Provide screenshots of CHAMAlink
   - Explain the business use case

2. **Update Environment**
   ```env
   QUICKBOOKS_ENVIRONMENT=production
   QUICKBOOKS_BASE_URL=https://quickbooks.api.intuit.com
   ```

3. **Update Redirect URI**
   - Add your production domain to app settings
   - Update environment variable

## 🎓 Learning Resources

### Intuit Documentation:
- [QuickBooks API Explorer](https://developer.intuit.com/app/developer/qbo/docs/api/accounting/most-commonly-used/customer)
- [OAuth 2.0 Guide](https://developer.intuit.com/app/developer/qbo/docs/develop/authentication-and-authorization/oauth_2.0)
- [Sandbox Tutorial](https://developer.intuit.com/app/developer/qbo/docs/develop/sandboxcompanies)

### Testing Tools:
- [API Explorer](https://developer.intuit.com/app/developer/qbo/docs/api/accounting) - Test API calls
- [Webhooks](https://developer.intuit.com/app/developer/qbo/docs/develop/webhooks) - Real-time notifications
- [Batch Operations](https://developer.intuit.com/app/developer/qbo/docs/develop/tutorials/batch_operations) - Bulk operations

## 🔒 Security Best Practices

### Credential Management:
- ✅ Never commit credentials to Git
- ✅ Use environment variables only
- ✅ Rotate secrets regularly
- ✅ Use HTTPS in production

### Token Handling:
- ✅ Access tokens expire in 1 hour
- ✅ Refresh tokens valid for 100 days  
- ✅ CHAMAlink handles this automatically
- ✅ Tokens stored encrypted in database

## 🆘 Common Setup Issues

### 1. "Invalid Client ID"
**Problem**: Wrong credentials
**Solution**: Double-check Client ID from developer.intuit.com

### 2. "Redirect URI Mismatch"
**Problem**: URI doesn't match app settings
**Solution**: Ensure exact match including `http://` and port

### 3. "Sandbox Connection Failed"
**Problem**: Environment misconfiguration
**Solution**: Verify `QUICKBOOKS_ENVIRONMENT=sandbox`

### 4. "Scope Error"
**Problem**: Insufficient permissions
**Solution**: Request `com.intuit.quickbooks.accounting` scope

---

## ✅ Your Real Credentials Template

Replace these with your actual values from developer.intuit.com:

```env
# Get these from https://developer.intuit.com -> My Apps -> Keys & OAuth
QUICKBOOKS_CLIENT_ID=ABcd1234567890abcdef1234567890ab
QUICKBOOKS_CLIENT_SECRET=1234567890abcdef1234567890abcdef12345678

# Development settings
QUICKBOOKS_REDIRECT_URI=http://localhost:5000/integrations/accounting/quickbooks/callback
QUICKBOOKS_ENVIRONMENT=sandbox
QUICKBOOKS_BASE_URL=https://sandbox-quickbooks.api.intuit.com
```

**Next Step**: Copy your real credentials from Intuit Developer Console and update your `.env` file! 🎉
