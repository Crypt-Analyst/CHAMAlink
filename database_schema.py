"""
CHAMAlink Database Schema Documentation
=====================================

This document outlines the complete database schema for the CHAMAlink application.
"""

CHAMALINK_SCHEMA = """
# CHAMAlink Database Schema

## Core Tables

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    phone_number VARCHAR(20) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'member',
    is_super_admin BOOLEAN DEFAULT FALSE,
    
    -- Personal Information
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    date_of_birth DATE,
    national_id VARCHAR(20) UNIQUE,
    passport_number VARCHAR(20) UNIQUE,
    
    -- Account Security
    is_email_verified BOOLEAN DEFAULT FALSE,
    is_documents_verified BOOLEAN DEFAULT FALSE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until DATETIME,
    
    -- Password Reset
    password_reset_token VARCHAR(100) UNIQUE,
    password_reset_expires DATETIME,
    
    -- Guardian Information (for users under 18)
    is_minor BOOLEAN DEFAULT FALSE,
    guardian_name VARCHAR(100),
    guardian_phone VARCHAR(20),
    guardian_id VARCHAR(20),
    guardian_relationship VARCHAR(50),
    
    -- Location Information
    country_code VARCHAR(2),
    country_name VARCHAR(100),
    city VARCHAR(100),
    timezone VARCHAR(50) DEFAULT 'Africa/Nairobi',
    
    -- User Preferences
    preferred_language VARCHAR(5) DEFAULT 'en',
    preferred_theme VARCHAR(20) DEFAULT 'light',
    preferred_font VARCHAR(20) DEFAULT 'default',
    preferred_currency VARCHAR(3) DEFAULT 'KES',
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    is_active BOOLEAN DEFAULT TRUE,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Chamas Table
```sql
CREATE TABLE chamas (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    creator_id INTEGER NOT NULL,
    
    -- Financial Settings
    base_currency VARCHAR(3) DEFAULT 'KES',
    multi_currency_enabled BOOLEAN DEFAULT FALSE,
    
    -- Chama Rules
    contribution_amount FLOAT,
    contribution_frequency VARCHAR(20),
    late_fee_amount FLOAT,
    meeting_frequency VARCHAR(20),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (creator_id) REFERENCES users(id)
);
```

### Chama Members Table
```sql
CREATE TABLE chama_members (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    chama_id INTEGER NOT NULL,
    role VARCHAR(20) DEFAULT 'member',
    is_active BOOLEAN DEFAULT TRUE,
    joined_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    left_date DATETIME,
    
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (chama_id) REFERENCES chamas(id),
    UNIQUE(user_id, chama_id)
);
```

## Financial Tables

### Transactions Table
```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    chama_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    amount FLOAT NOT NULL,
    description TEXT,
    reference_number VARCHAR(100),
    payment_method VARCHAR(50),
    
    -- Multi-currency support
    currency VARCHAR(3) DEFAULT 'KES',
    exchange_rate FLOAT DEFAULT 1.0,
    original_amount FLOAT,
    
    -- Status and timestamps
    status VARCHAR(20) DEFAULT 'pending',
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (chama_id) REFERENCES chamas(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Contributions Table
```sql
CREATE TABLE contributions (
    id INTEGER PRIMARY KEY,
    chama_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    amount FLOAT NOT NULL,
    contribution_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    payment_method VARCHAR(50),
    reference_number VARCHAR(100),
    
    -- Multi-currency support
    currency VARCHAR(3) DEFAULT 'KES',
    exchange_rate FLOAT DEFAULT 1.0,
    original_amount FLOAT,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending',
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (chama_id) REFERENCES chamas(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Loans Table
```sql
CREATE TABLE loans (
    id INTEGER PRIMARY KEY,
    chama_id INTEGER NOT NULL,
    borrower_id INTEGER NOT NULL,
    approved_by INTEGER,
    
    -- Loan Details
    principal_amount FLOAT NOT NULL,
    interest_rate FLOAT DEFAULT 0.0,
    total_amount FLOAT NOT NULL,
    
    -- Multi-currency support
    currency VARCHAR(3) DEFAULT 'KES',
    exchange_rate FLOAT DEFAULT 1.0,
    
    -- Terms
    loan_term_months INTEGER,
    monthly_payment FLOAT,
    
    -- Status and dates
    status VARCHAR(20) DEFAULT 'pending',
    application_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    approval_date DATETIME,
    disbursement_date DATETIME,
    due_date DATETIME,
    
    -- Repayment tracking
    amount_paid FLOAT DEFAULT 0.0,
    remaining_balance FLOAT,
    
    FOREIGN KEY (chama_id) REFERENCES chamas(id),
    FOREIGN KEY (borrower_id) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);
```

### Loan Payments Table
```sql
CREATE TABLE loan_payments (
    id INTEGER PRIMARY KEY,
    loan_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    amount FLOAT NOT NULL,
    payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    payment_method VARCHAR(50),
    reference_number VARCHAR(100),
    
    -- Multi-currency support
    currency VARCHAR(3) DEFAULT 'KES',
    exchange_rate FLOAT DEFAULT 1.0,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending',
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (loan_id) REFERENCES loans(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## Subscription Tables

### Subscription Plans Table
```sql
CREATE TABLE subscription_plans (
    id INTEGER PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Pricing (multi-currency)
    price_kes FLOAT,
    price_usd FLOAT,
    price_eur FLOAT,
    price_tzs FLOAT,
    price_ugx FLOAT,
    price_gbp FLOAT,
    
    -- Plan limits
    duration_months INTEGER DEFAULT 1,
    max_chamas INTEGER DEFAULT -1,
    max_members_per_chama INTEGER DEFAULT -1,
    max_transactions_per_month INTEGER DEFAULT -1,
    
    -- Features
    features TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Subscriptions Table
```sql
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    plan_id INTEGER NOT NULL,
    
    -- Subscription period
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    
    -- Status
    status VARCHAR(20) DEFAULT 'active',
    payment_status VARCHAR(20) DEFAULT 'pending',
    
    -- Payment details
    currency VARCHAR(3) DEFAULT 'KES',
    amount_paid FLOAT DEFAULT 0.0,
    payment_method VARCHAR(50),
    
    -- Trial information
    is_trial BOOLEAN DEFAULT FALSE,
    trial_end_date DATETIME,
    
    -- Auto-renewal
    auto_renew BOOLEAN DEFAULT TRUE,
    renewal_attempts INTEGER DEFAULT 0,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (plan_id) REFERENCES subscription_plans(id)
);
```

## Notification Tables

### Notifications Table
```sql
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    chama_id INTEGER,
    
    -- Notification content
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    
    -- Status
    is_read BOOLEAN DEFAULT FALSE,
    is_email_sent BOOLEAN DEFAULT FALSE,
    is_sms_sent BOOLEAN DEFAULT FALSE,
    
    -- Priority and category
    priority VARCHAR(20) DEFAULT 'normal',
    category VARCHAR(50),
    
    -- Actions
    action_url VARCHAR(500),
    action_text VARCHAR(100),
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    read_at DATETIME,
    
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (chama_id) REFERENCES chamas(id)
);
```

## Security Tables

### Security Events Table
```sql
CREATE TABLE security_events (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    event_type VARCHAR(50) NOT NULL,
    event_description TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    location VARCHAR(100),
    
    -- Risk assessment
    risk_level VARCHAR(20) DEFAULT 'low',
    is_suspicious BOOLEAN DEFAULT FALSE,
    
    -- Response
    action_taken VARCHAR(100),
    is_resolved BOOLEAN DEFAULT FALSE,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Two-Factor Authentication Table
```sql
CREATE TABLE two_factor_auth (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    secret_key VARCHAR(100) NOT NULL,
    is_enabled BOOLEAN DEFAULT FALSE,
    backup_codes TEXT,
    last_used DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## Payment Integration Tables

### M-Pesa Transactions Table
```sql
CREATE TABLE mpesa_transactions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    chama_id INTEGER,
    
    -- M-Pesa details
    phone_number VARCHAR(20) NOT NULL,
    amount FLOAT NOT NULL,
    mpesa_receipt_number VARCHAR(50),
    transaction_id VARCHAR(100),
    
    -- Integration details
    checkout_request_id VARCHAR(100),
    merchant_request_id VARCHAR(100),
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending',
    result_code INTEGER,
    result_desc TEXT,
    
    -- Timestamps
    initiated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (chama_id) REFERENCES chamas(id)
);
```

## Audit and Logging Tables

### Audit Log Table
```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    chama_id INTEGER,
    
    -- Action details
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(50),
    record_id INTEGER,
    
    -- Changes
    old_values TEXT,
    new_values TEXT,
    
    -- Context
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (chama_id) REFERENCES chamas(id)
);
```

## Relationships Summary

1. **Users → Chamas**: One-to-Many (via creator_id)
2. **Users ↔ Chamas**: Many-to-Many (via chama_members)
3. **Chamas → Transactions**: One-to-Many
4. **Chamas → Contributions**: One-to-Many
5. **Chamas → Loans**: One-to-Many
6. **Users → Subscriptions**: One-to-Many
7. **Users → Notifications**: One-to-Many
8. **Users → Security Events**: One-to-Many
9. **Loans → Loan Payments**: One-to-Many
10. **Users → M-Pesa Transactions**: One-to-Many

## Key Features

### Multi-Currency Support
- All financial tables include currency, exchange_rate, and original_amount fields
- Automatic conversion using real-time exchange rates
- Support for KES, USD, EUR, TZS, UGX, GBP

### Security Features
- Comprehensive audit logging
- Security event tracking
- Two-factor authentication support
- Password reset mechanism
- Account lockout protection

### Subscription Management
- Flexible multi-tier subscription plans
- Multi-currency pricing
- Trial period support
- Auto-renewal functionality
- Usage tracking and limits

### Payment Integration
- M-Pesa integration for East African markets
- Multiple payment method support
- Transaction status tracking
- Receipt management

This schema supports a fully-featured chama management system with international capabilities, robust security, and comprehensive financial tracking.
"""

def generate_schema_diagram():
    """Generate a visual representation of the database schema"""
    
    schema_markdown = """
# CHAMAlink Database Schema Diagram

```mermaid
erDiagram
    USERS {
        int id PK
        string username UK
        string email UK
        string phone_number UK
        string password_hash
        string role
        boolean is_super_admin
        string first_name
        string last_name
        date date_of_birth
        string country_code
        string country_name
        string preferred_currency
        datetime created_at
        boolean is_active
    }
    
    CHAMAS {
        int id PK
        string name
        text description
        int creator_id FK
        string base_currency
        boolean multi_currency_enabled
        float contribution_amount
        string contribution_frequency
        boolean is_active
        datetime created_at
    }
    
    CHAMA_MEMBERS {
        int id PK
        int user_id FK
        int chama_id FK
        string role
        boolean is_active
        datetime joined_date
    }
    
    TRANSACTIONS {
        int id PK
        int chama_id FK
        int user_id FK
        string transaction_type
        float amount
        string currency
        float exchange_rate
        string payment_method
        string status
        datetime transaction_date
    }
    
    CONTRIBUTIONS {
        int id PK
        int chama_id FK
        int user_id FK
        float amount
        string currency
        string payment_method
        string status
        datetime contribution_date
    }
    
    LOANS {
        int id PK
        int chama_id FK
        int borrower_id FK
        float principal_amount
        float interest_rate
        string currency
        string status
        datetime application_date
        float amount_paid
    }
    
    LOAN_PAYMENTS {
        int id PK
        int loan_id FK
        int user_id FK
        float amount
        string currency
        string payment_method
        datetime payment_date
    }
    
    SUBSCRIPTION_PLANS {
        int id PK
        string name UK
        string display_name
        float price_kes
        float price_usd
        int max_chamas
        int max_members_per_chama
        boolean is_active
    }
    
    SUBSCRIPTIONS {
        int id PK
        int user_id FK
        int plan_id FK
        datetime start_date
        datetime end_date
        string status
        string currency
        float amount_paid
        boolean is_trial
    }
    
    NOTIFICATIONS {
        int id PK
        int user_id FK
        int chama_id FK
        string title
        text message
        string notification_type
        boolean is_read
        datetime created_at
    }
    
    MPESA_TRANSACTIONS {
        int id PK
        int user_id FK
        int chama_id FK
        string phone_number
        float amount
        string mpesa_receipt_number
        string status
        datetime initiated_at
    }
    
    SECURITY_EVENTS {
        int id PK
        int user_id FK
        string event_type
        string ip_address
        string risk_level
        boolean is_suspicious
        datetime created_at
    }
    
    %% Relationships
    USERS ||--o{ CHAMAS : "creates"
    USERS ||--o{ CHAMA_MEMBERS : "joins"
    CHAMAS ||--o{ CHAMA_MEMBERS : "has"
    CHAMAS ||--o{ TRANSACTIONS : "contains"
    CHAMAS ||--o{ CONTRIBUTIONS : "receives"
    CHAMAS ||--o{ LOANS : "manages"
    USERS ||--o{ TRANSACTIONS : "makes"
    USERS ||--o{ CONTRIBUTIONS : "pays"
    USERS ||--o{ LOANS : "borrows"
    LOANS ||--o{ LOAN_PAYMENTS : "repaid_by"
    USERS ||--o{ LOAN_PAYMENTS : "makes"
    USERS ||--o{ SUBSCRIPTIONS : "subscribes"
    SUBSCRIPTION_PLANS ||--o{ SUBSCRIPTIONS : "defines"
    USERS ||--o{ NOTIFICATIONS : "receives"
    CHAMAS ||--o{ NOTIFICATIONS : "generates"
    USERS ||--o{ MPESA_TRANSACTIONS : "initiates"
    CHAMAS ||--o{ MPESA_TRANSACTIONS : "for"
    USERS ||--o{ SECURITY_EVENTS : "triggers"
```

## Schema Statistics

- **Total Tables**: 12 core tables
- **Primary Relationships**: 15 foreign key relationships
- **Multi-Currency Tables**: 6 tables with currency support
- **Audit Tables**: 2 security and logging tables
- **User-Centric Design**: 8 tables directly related to users
- **Financial Tables**: 5 tables for financial operations

## Key Design Principles

1. **Normalization**: 3NF compliance for data integrity
2. **Multi-Currency**: Native support for international operations
3. **Audit Trail**: Comprehensive logging for compliance
4. **Security First**: Built-in security monitoring
5. **Scalability**: Designed for growth and expansion
6. **Flexibility**: Configurable plans and preferences
"""
    
    return schema_markdown

if __name__ == '__main__':
    print("CHAMAlink Database Schema")
    print("=" * 50)
    print(CHAMALINK_SCHEMA)
    print("\n" + "=" * 50)
    print(generate_schema_diagram())
