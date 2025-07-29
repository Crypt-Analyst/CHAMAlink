"""
CHAMAlink Simple Performance Optimization
=========================================
Basic performance optimizations without external dependencies
"""

import os
from functools import wraps
import time
import hashlib
from collections import defaultdict

class SimpleCache:
    """Simple in-memory cache implementation"""
    
    def __init__(self, default_timeout=300):
        self.cache = {}
        self.timeouts = {}
        self.default_timeout = default_timeout
    
    def get(self, key):
        """Get value from cache"""
        if key in self.cache:
            if time.time() < self.timeouts.get(key, 0):
                return self.cache[key]
            else:
                # Expired
                self.delete(key)
        return None
    
    def set(self, key, value, timeout=None):
        """Set value in cache"""
        if timeout is None:
            timeout = self.default_timeout
        
        self.cache[key] = value
        self.timeouts[key] = time.time() + timeout
    
    def delete(self, key):
        """Delete key from cache"""
        self.cache.pop(key, None)
        self.timeouts.pop(key, None)
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.timeouts.clear()

class SimplePerformanceOptimizer:
    """Simple performance optimizer without external dependencies"""
    
    def __init__(self, app=None):
        self.app = app
        self.cache = SimpleCache()
        self.query_cache = SimpleCache(600)  # 10 minutes for queries
        self.template_cache = SimpleCache(1800)  # 30 minutes for templates
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        
        # Configure template caching
        app.jinja_env.cache_size = 400
        app.jinja_env.auto_reload = False if not app.debug else True
        
        # Add performance optimizations to app config
        app.config.setdefault('SQLALCHEMY_ENGINE_OPTIONS', {
            'pool_pre_ping': True,
            'pool_recycle': 3600,
        })
        
        print("✅ Simple Performance Optimization: IMPLEMENTED")
        print("✅ Template Caching: IMPLEMENTED") 
        print("✅ Database Connection Pooling: IMPLEMENTED")
        print("✅ Caching System: IMPLEMENTED")
    
    def cache_key(self, *args):
        """Generate cache key from arguments"""
        key_string = '_'.join(str(arg) for arg in args)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def cache_user_data(self, user_id, data, timeout=300):
        """Cache user-specific data"""
        key = self.cache_key('user', user_id)
        self.cache.set(key, data, timeout)
    
    def get_cached_user_data(self, user_id):
        """Get cached user data"""
        key = self.cache_key('user', user_id)
        return self.cache.get(key)
    
    def cache_chama_data(self, chama_id, data, timeout=600):
        """Cache chama-specific data"""
        key = self.cache_key('chama', chama_id)
        self.cache.set(key, data, timeout)
    
    def get_cached_chama_data(self, chama_id):
        """Get cached chama data"""
        key = self.cache_key('chama', chama_id)
        return self.cache.get(key)
    
    def cache_analytics_data(self, query_hash, data, timeout=900):
        """Cache analytics data"""
        key = self.cache_key('analytics', query_hash)
        self.query_cache.set(key, data, timeout)
    
    def get_cached_analytics(self, query_hash):
        """Get cached analytics data"""
        key = self.cache_key('analytics', query_hash)
        return self.query_cache.get(key)
    
    def invalidate_user_cache(self, user_id):
        """Invalidate user cache"""
        key = self.cache_key('user', user_id)
        self.cache.delete(key)
    
    def invalidate_chama_cache(self, chama_id):
        """Invalidate chama cache"""
        key = self.cache_key('chama', chama_id)
        self.cache.delete(key)
    
    def clear_all_cache(self):
        """Clear all caches"""
        self.cache.clear()
        self.query_cache.clear()
        self.template_cache.clear()

# Performance decorators
def simple_cache(timeout=300):
    """Simple caching decorator"""
    def decorator(f):
        cache = SimpleCache(timeout)
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Create cache key
            key = hashlib.md5(f"{f.__name__}_{args}_{kwargs}".encode()).hexdigest()
            
            # Try cache first
            result = cache.get(key)
            if result is not None:
                return result
            
            # Execute and cache
            result = f(*args, **kwargs)
            cache.set(key, result, timeout)
            return result
        
        return decorated_function
    return decorator

def cache_template(timeout=600):
    """Template caching decorator"""
    def decorator(f):
        cache = SimpleCache(timeout)
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import request
            
            # Create cache key from URL and function
            key = hashlib.md5(f"{f.__name__}_{request.url}".encode()).hexdigest()
            
            # Try cache first
            result = cache.get(key)
            if result is not None:
                return result
            
            # Execute and cache
            result = f(*args, **kwargs)
            cache.set(key, result, timeout)
            return result
        
        return decorated_function
    return decorator

# Async operation helpers
class BackgroundTaskManager:
    """Simple background task manager"""
    
    def __init__(self):
        self.tasks = []
    
    def add_task(self, func, *args, **kwargs):
        """Add a background task"""
        self.tasks.append((func, args, kwargs))
    
    def process_tasks(self):
        """Process all pending tasks"""
        for func, args, kwargs in self.tasks:
            try:
                func(*args, **kwargs)
            except Exception as e:
                print(f"Background task error: {e}")
        self.tasks.clear()

# Database optimization helpers
class SimpleQueryOptimizer:
    """Simple query optimization utilities"""
    
    @staticmethod
    def batch_load_users(user_ids):
        """Batch load users"""
        from app.models import User
        if not user_ids:
            return {}
        
        users = User.query.filter(User.id.in_(user_ids)).all()
        return {user.id: user for user in users}
    
    @staticmethod
    def batch_load_chamas(chama_ids):
        """Batch load chamas"""
        from app.models import Chama
        if not chama_ids:
            return {}
        
        chamas = Chama.query.filter(Chama.id.in_(chama_ids)).all()
        return {chama.id: chama for chama in chamas}

# Export simple performance optimizer
simple_performance_optimizer = SimplePerformanceOptimizer()
background_tasks = BackgroundTaskManager()

print("🚀 Simple Performance Module: LOADED")
