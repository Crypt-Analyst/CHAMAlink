#!/usr/bin/env python3
"""
Simple database migration to add missing mobile device fields to users table
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

# Set up minimal Flask app for database operations
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///instance/chamalink.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

def add_mobile_fields():
    """Add mobile device fields to users table"""
    try:
        with app.app_context():
            # Check if columns already exist
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name IN ('mobile_device_id', 'mobile_device_token', 'mobile_device_type', 'last_mobile_sync')
            """))
            existing_columns = [row[0] for row in result.fetchall()]
            
            # Add missing mobile device fields
            if 'mobile_device_id' not in existing_columns:
                db.session.execute(text("ALTER TABLE users ADD COLUMN mobile_device_id VARCHAR(255)"))
                print("✅ Added mobile_device_id column")
            
            if 'mobile_device_token' not in existing_columns:
                db.session.execute(text("ALTER TABLE users ADD COLUMN mobile_device_token VARCHAR(500)"))
                print("✅ Added mobile_device_token column")
            
            if 'mobile_device_type' not in existing_columns:
                db.session.execute(text("ALTER TABLE users ADD COLUMN mobile_device_type VARCHAR(50)"))
                print("✅ Added mobile_device_type column")
            
            if 'last_mobile_sync' not in existing_columns:
                db.session.execute(text("ALTER TABLE users ADD COLUMN last_mobile_sync TIMESTAMP"))
                print("✅ Added last_mobile_sync column")
            
            # Add currency table if it doesn't exist
            try:
                db.session.execute(text("""
                    CREATE TABLE IF NOT EXISTS currencies (
                        id SERIAL PRIMARY KEY,
                        code VARCHAR(3) NOT NULL UNIQUE,
                        name VARCHAR(50) NOT NULL,
                        symbol VARCHAR(5) NOT NULL,
                        exchange_rate_to_usd FLOAT NOT NULL DEFAULT 1.0,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                print("✅ Created currencies table")
                
                # Insert default currencies
                db.session.execute(text("""
                    INSERT INTO currencies (code, name, symbol, exchange_rate_to_usd) VALUES
                    ('USD', 'US Dollar', '$', 1.0),
                    ('KES', 'Kenyan Shilling', 'KSh', 0.0077),
                    ('UGX', 'Ugandan Shilling', 'USh', 0.00027),
                    ('TZS', 'Tanzanian Shilling', 'TSh', 0.00043),
                    ('EUR', 'Euro', '€', 1.09),
                    ('GBP', 'British Pound', '£', 1.27)
                    ON CONFLICT (code) DO NOTHING
                """))
                print("✅ Seeded default currencies")
                
            except Exception as e:
                print(f"⚠️ Currency table setup: {e}")
            
            # Add currency foreign keys to chamas and transactions if tables exist
            try:
                # Check if chamas table exists
                result = db.session.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_name = 'chamas'
                """))
                if result.fetchone():
                    # Check if default_currency_id column exists
                    result = db.session.execute(text("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'chamas' AND column_name = 'default_currency_id'
                    """))
                    if not result.fetchone():
                        db.session.execute(text("ALTER TABLE chamas ADD COLUMN default_currency_id INTEGER REFERENCES currencies(id)"))
                        print("✅ Added default_currency_id to chamas table")
                
                # Check if transactions table exists
                result = db.session.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_name = 'transactions'
                """))
                if result.fetchone():
                    # Check if currency_id column exists
                    result = db.session.execute(text("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'transactions' AND column_name = 'currency_id'
                    """))
                    if not result.fetchone():
                        db.session.execute(text("ALTER TABLE transactions ADD COLUMN currency_id INTEGER REFERENCES currencies(id)"))
                        print("✅ Added currency_id to transactions table")
                        
            except Exception as e:
                print(f"⚠️ Foreign key setup: {e}")
            
            db.session.commit()
            print("✅ All database migrations completed successfully!")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.session.rollback()
        raise

if __name__ == '__main__':
    print("🔧 Running database migration...")
    add_mobile_fields()
    print("🎉 Migration completed!")
