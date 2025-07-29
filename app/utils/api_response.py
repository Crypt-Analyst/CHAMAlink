"""
Mobile API Response Standardization
==================================
Standardized response format for all mobile API endpoints
"""

from flask import jsonify
from datetime import datetime
import traceback

class APIResponse:
    """Standardized API response handler"""
    
    @staticmethod
    def success(data=None, message="Success", status_code=200, meta=None):
        """Standard success response"""
        response = {
            "success": True,
            "status": "success",
            "status_code": status_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": data or {}
        }
        
        if meta:
            response["meta"] = meta
            
        return jsonify(response), status_code
    
    @staticmethod
    def error(message="An error occurred", status_code=400, error_code=None, details=None):
        """Standard error response"""
        response = {
            "success": False,
            "status": "error",
            "status_code": status_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": {
                "code": error_code or f"E{status_code}",
                "message": message,
                "details": details
            }
        }
        
        return jsonify(response), status_code
    
    @staticmethod
    def validation_error(errors, message="Validation failed"):
        """Standard validation error response"""
        return APIResponse.error(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details={"validation_errors": errors}
        )
    
    @staticmethod
    def unauthorized(message="Authentication required"):
        """Standard unauthorized response"""
        return APIResponse.error(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED"
        )
    
    @staticmethod
    def forbidden(message="Access denied"):
        """Standard forbidden response"""
        return APIResponse.error(
            message=message,
            status_code=403,
            error_code="FORBIDDEN"
        )
    
    @staticmethod
    def not_found(message="Resource not found"):
        """Standard not found response"""
        return APIResponse.error(
            message=message,
            status_code=404,
            error_code="NOT_FOUND"
        )
    
    @staticmethod
    def server_error(message="Internal server error", details=None):
        """Standard server error response"""
        return APIResponse.error(
            message=message,
            status_code=500,
            error_code="INTERNAL_ERROR",
            details=details
        )
    
    @staticmethod
    def paginated_success(data, page=1, per_page=10, total=0, message="Success"):
        """Standard paginated response"""
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        
        meta = {
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
        
        return APIResponse.success(data=data, message=message, meta=meta)

class APIValidator:
    """API input validation helpers"""
    
    @staticmethod
    def validate_required_fields(data, required_fields):
        """Validate required fields in request data"""
        if not data:
            return ["Request body is required"]
        
        errors = []
        for field in required_fields:
            if field not in data or not data.get(field):
                errors.append(f"Field '{field}' is required")
        
        return errors
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone(phone):
        """Validate phone number format"""
        import re
        # Basic phone validation - can be enhanced
        pattern = r'^\+?[1-9]\d{1,14}$'
        return re.match(pattern, phone.replace(' ', '').replace('-', '')) is not None

def handle_api_exceptions(f):
    """Decorator to handle API exceptions with standardized responses"""
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            return APIResponse.validation_error(
                errors=[str(e)],
                message="Invalid input data"
            )
        except PermissionError as e:
            return APIResponse.forbidden(str(e))
        except FileNotFoundError as e:
            return APIResponse.not_found(str(e))
        except Exception as e:
            # Log the full traceback for debugging
            error_details = {
                "exception_type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
            
            return APIResponse.server_error(
                message="An unexpected error occurred",
                details=error_details
            )
    
    decorated_function.__name__ = f.__name__
    return decorated_function

# Standard response status codes
class StatusCode:
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    VALIDATION_ERROR = 422
    INTERNAL_ERROR = 500

print("✅ Mobile API Response Standardization: LOADED")
