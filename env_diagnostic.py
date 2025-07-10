#!/usr/bin/env python3
"""
Environment Variables Diagnostic
"""

import os
from dotenv import load_dotenv

print("🔍 Environment Variables Diagnostic")
print("="*50)

# Load environment variables
load_dotenv()

# Check all email-related environment variables
email_vars = [
    'MAIL_SERVER',
    'MAIL_PORT', 
    'MAIL_USE_TLS',
    'MAIL_USE_SSL',
    'MAIL_USERNAME',
    'MAIL_PASSWORD',
    'MAIL_DEFAULT_SENDER',
    'EMAIL_USERNAME',
    'EMAIL_PASSWORD',
    'EMAIL_SERVER',
    'EMAIL_PORT'
]

for var in email_vars:
    value = os.getenv(var)
    if value:
        # Hide password for security
        if 'PASSWORD' in var:
            print(f"{var}: {'*' * len(value)} (length: {len(value)})")
        else:
            print(f"{var}: {value}")
    else:
        print(f"{var}: NOT SET")

print("\n" + "="*50)

# Test the specific credentials that our EmailService uses
print("🔧 EmailService Configuration:")
smtp_server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
port = int(os.getenv('MAIL_PORT', '587'))
sender_email = os.getenv('MAIL_USERNAME', 'rahasoft.app@gmail.com')
password = os.getenv('MAIL_PASSWORD')
use_tls = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'

print(f"SMTP Server: {smtp_server}")
print(f"Port: {port}")
print(f"Sender Email: {sender_email}")
print(f"Password: {'*' * len(password) if password else 'NOT SET'} (length: {len(password) if password else 0})")
print(f"Use TLS: {use_tls}")

print("\n" + "="*50)
print("✅ Diagnostic complete")
