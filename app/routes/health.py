from flask import Blueprint, jsonify, request
from app import db
from app.models.user import User
import os
import traceback

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """Health check endpoint to diagnose 500 errors"""
    try:
        # Test database connection
        db.engine.execute('SELECT 1')
        db_status = "✅ Connected"
        
        # Test if tables exist
        try:
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            table_status = f"✅ Found {len(tables)} tables"
        except:
            table_status = "❌ Cannot read tables"
        
        # Test user table specifically
        try:
            user_count = User.query.count()
            user_status = f"✅ {user_count} users"
        except Exception as e:
            user_status = f"❌ User table error: {str(e)}"
        
        return jsonify({
            'status': 'healthy',
            'database': db_status,
            'tables': table_status,
            'users': user_status,
            'environment': os.environ.get('FLASK_DEBUG', 'unknown'),
            'secret_key_set': bool(os.environ.get('SECRET_KEY'))
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
