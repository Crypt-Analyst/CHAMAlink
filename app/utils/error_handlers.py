"""
Simple error handling and debugging for ChamaLink
"""
from flask import jsonify, render_template, current_app, request
import traceback
import logging

def init_error_handlers(app):
    """Initialize error handlers for debugging"""
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 internal server errors with detailed info"""
        try:
            # Log the error
            app.logger.error(f"500 Internal Server Error: {str(error)}")
            app.logger.error(f"Request URL: {request.url}")
            app.logger.error(f"Request method: {request.method}")
            app.logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Return JSON response for API endpoints
            if request.path.startswith('/api/') or request.content_type == 'application/json':
                return jsonify({
                    'error': 'Internal Server Error',
                    'message': str(error),
                    'debug_info': traceback.format_exc() if app.debug else None
                }), 500
            
            # Return HTML response for regular pages
            return render_template('errors/500.html', 
                                 error=str(error) if app.debug else "Something went wrong"), 500
                                 
        except Exception as e:
            # If error handling itself fails, return basic response
            return f"Critical Error: {str(e)}<br>Original Error: {str(error)}", 500
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 not found errors"""
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 forbidden errors"""
        return render_template('errors/403.html'), 403
