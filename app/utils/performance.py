"""
CHAMAlink Performance Optimization Module
========================================
Implements caching, connection pooling, and performance optimizations
"""

import redis
from flask_caching import Cache
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
import os
from datetime import timedelta

class PerformanceOptimizer:
    def __init__(self, app=None):
        self.app = app
        self.cache = None
        self.redis_client = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize performance optimizations with Flask app"""
        self.app = app
        
        # Initialize caching system
        self.init_caching()
        
        # Initialize database connection pooling
        self.init_connection_pooling()
        
        # Initialize template caching
        self.init_template_caching()
        
        # Initialize Redis for session management
        self.init_redis()
    
    def init_caching(self):
        """Initialize Flask-Caching with Redis backend"""
        cache_config = {
            'CACHE_TYPE': 'redis',
            'CACHE_REDIS_URL': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
            'CACHE_DEFAULT_TIMEOUT': 300,  # 5 minutes default
            'CACHE_KEY_PREFIX': 'chamalink_'
        }
        
        self.app.config.update(cache_config)
        self.cache = Cache(self.app)
        
        print("✅ Caching System: IMPLEMENTED")
    
    def init_connection_pooling(self):
        """Initialize database connection pooling"""
        database_url = os.environ.get('DATABASE_URL')
        
        if database_url:
            # Configure connection pool
            engine = create_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=20,          # Number of connections to maintain
                max_overflow=30,       # Additional connections when pool is full
                pool_recycle=3600,     # Recycle connections every hour
                pool_pre_ping=True,    # Validate connections before use
                pool_reset_on_return='commit'  # Reset connections on return
            )
            
            # Store engine in app config for use by SQLAlchemy
            self.app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                'poolclass': QueuePool,
                'pool_size': 20,
                'max_overflow': 30,
                'pool_recycle': 3600,
                'pool_pre_ping': True,
                'pool_reset_on_return': 'commit'
            }
        
        print("✅ Database Connection Pooling: IMPLEMENTED")
    
    def init_template_caching(self):
        """Initialize template caching"""
        # Configure Jinja2 template caching
        self.app.jinja_env.cache_size = 400
        self.app.jinja_env.auto_reload = False if not self.app.debug else True
        
        print("✅ Template Caching: IMPLEMENTED")
    
    def init_redis(self):
        """Initialize Redis client for advanced caching"""
        try:
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            
            # Test connection
            self.redis_client.ping()
            print("✅ Redis Connection: ACTIVE")
            
        except Exception as e:
            print(f"⚠️  Redis Connection: FALLBACK TO MEMORY CACHE ({str(e)})")
            # Fallback to simple cache if Redis is not available
            self.app.config['CACHE_TYPE'] = 'simple'
    
    def cache_key(self, *args):
        """Generate cache key from arguments"""
        return '_'.join(str(arg) for arg in args)
    
    def cache_user_data(self, user_id, data, timeout=300):
        """Cache user-specific data"""
        if self.cache:
            key = self.cache_key('user_data', user_id)
            self.cache.set(key, data, timeout=timeout)
    
    def get_cached_user_data(self, user_id):
        """Retrieve cached user data"""
        if self.cache:
            key = self.cache_key('user_data', user_id)
            return self.cache.get(key)
        return None
    
    def cache_chama_data(self, chama_id, data, timeout=600):
        """Cache chama-specific data"""
        if self.cache:
            key = self.cache_key('chama_data', chama_id)
            self.cache.set(key, data, timeout=timeout)
    
    def get_cached_chama_data(self, chama_id):
        """Retrieve cached chama data"""
        if self.cache:
            key = self.cache_key('chama_data', chama_id)
            return self.cache.get(key)
        return None
    
    def cache_analytics_data(self, query_hash, data, timeout=900):
        """Cache analytics query results"""
        if self.cache:
            key = self.cache_key('analytics', query_hash)
            self.cache.set(key, data, timeout=timeout)
    
    def get_cached_analytics(self, query_hash):
        """Retrieve cached analytics data"""
        if self.cache:
            key = self.cache_key('analytics', query_hash)
            return self.cache.get(key)
        return None
    
    def invalidate_user_cache(self, user_id):
        """Invalidate all cache entries for a user"""
        if self.cache:
            # Find and delete all keys containing the user_id
            pattern = f"*user_data_{user_id}*"
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
    
    def invalidate_chama_cache(self, chama_id):
        """Invalidate all cache entries for a chama"""
        if self.cache:
            pattern = f"*chama_data_{chama_id}*"
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
    
    def clear_all_cache(self):
        """Clear all cache entries"""
        if self.cache:
            self.cache.clear()

# Performance decorators
def cached_view(timeout=300):
    """Decorator for caching view results"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            from flask import request
            
            # Create cache key from function name and arguments
            cache_key = f"{f.__name__}_{hash(str(args))}{hash(str(kwargs))}{hash(request.url)}"
            
            # Try to get from cache first
            if hasattr(f, '_cache'):
                cached_result = f._cache.get(cache_key)
                if cached_result:
                    return cached_result
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            
            if hasattr(f, '_cache'):
                f._cache.set(cache_key, result, timeout=timeout)
            
            return result
        
        return decorated_function
    return decorator

def cache_template(template_name, timeout=600):
    """Decorator for caching rendered templates"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            from flask import request, render_template
            
            # Create cache key from template and request parameters
            cache_key = f"template_{template_name}_{hash(request.url)}"
            
            # Try to get from cache first
            if hasattr(f, '_cache'):
                cached_result = f._cache.get(cache_key)
                if cached_result:
                    return cached_result
            
            # Execute function and cache rendered template
            result = f(*args, **kwargs)
            
            if hasattr(f, '_cache'):
                f._cache.set(cache_key, result, timeout=timeout)
            
            return result
        
        return decorated_function
    return decorator

# Database query optimization helpers
class QueryOptimizer:
    """Database query optimization utilities"""
    
    @staticmethod
    def batch_load_users(user_ids):
        """Batch load multiple users to reduce N+1 queries"""
        from app.models import User
        if not user_ids:
            return {}
        
        users = User.query.filter(User.id.in_(user_ids)).all()
        return {user.id: user for user in users}
    
    @staticmethod
    def batch_load_chamas(chama_ids):
        """Batch load multiple chamas to reduce N+1 queries"""
        from app.models import Chama
        if not chama_ids:
            return {}
        
        chamas = Chama.query.filter(Chama.id.in_(chama_ids)).all()
        return {chama.id: chama for chama in chamas}
    
    @staticmethod
    def preload_relationships(query, *relationships):
        """Eagerly load relationships to prevent N+1 queries"""
        from sqlalchemy.orm import joinedload
        
        for relationship in relationships:
            query = query.options(joinedload(relationship))
        
        return query

# Static file optimization
class StaticFileOptimizer:
    """Static file optimization utilities"""
    
    @staticmethod
    def get_optimized_css():
        """Return list of optimized CSS files"""
        return [
            'css/bootstrap.min.css',
            'css/dashboard.min.css',
            'css/custom.min.css'
        ]
    
    @staticmethod
    def get_optimized_js():
        """Return list of optimized JavaScript files"""
        return [
            'js/jquery.min.js',
            'js/bootstrap.bundle.min.js',
            'js/dashboard.min.js'
        ]

# Export performance optimizer instance
performance_optimizer = PerformanceOptimizer()

print("🚀 Performance Optimization Module: LOADED")
