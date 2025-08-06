import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Get database URL - prioritize SQLALCHEMY_DATABASE_URI
database_url = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
if database_url:
    os.environ["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    print("❌ No database URL found!")
    print("Available env vars:", [k for k in os.environ.keys() if 'DATABASE' in k.upper() or 'SQLALCHEMY' in k.upper()])

# Initialize core Flask extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

def create_app():
    from flask_login import current_user, logout_user
    app = Flask(__name__)

    @app.before_request
    def enforce_session_timeout():
        # Only check for authenticated users
        if current_user.is_authenticated:
            now = datetime.utcnow()
            last_active = session.get('last_active')
            timeout = app.config.get('PERMANENT_SESSION_LIFETIME', 1800)
            if last_active:
                last_active_dt = datetime.strptime(last_active, '%Y-%m-%dT%H:%M:%S')
                if (now - last_active_dt).total_seconds() > timeout:
                    logout_user()
                    flash('Session expired. Please log in again.', 'warning')
                    return redirect(url_for('auth.login'))
            # Update last_active timestamp
            session['last_active'] = now.strftime('%Y-%m-%dT%H:%M:%S')

    # Configuration
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "chamalink-secret-key")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    # Security Configuration - SSL/TLS
    is_production = os.getenv('FLASK_ENV', 'development').lower() == 'production'
    app.config['SESSION_COOKIE_SECURE'] = is_production  # Only send cookies over HTTPS in production
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent XSS attacks
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
    app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes
    
    # Force HTTPS in production
    if is_production:
        app.config['PREFERRED_URL_SCHEME'] = 'https'
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['REMEMBER_COOKIE_SECURE'] = True
        
    # Additional security headers
    @app.after_request
    def add_security_headers(response):
        # Enforce HTTPS in production
        if is_production:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # XSS Protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Content Security Policy (basic)
        response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' https: data: blob:; img-src 'self' https: data: blob:;"
        
        return response

    # Email configuration - Using TLS for security
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'  # Enable TLS
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@chamalink.com')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = 'auth.login'

    # Load user model
    try:
        from .models.user import User

        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))
    except ImportError:
        print("⚠️  User model not available")
    
    @login_manager.unauthorized_handler
    def unauthorized():
        if request.endpoint and request.endpoint != 'main.home':
            flash('Please log in to access this page.', 'info')
        return redirect(url_for('auth.login'))


    # Template context processor for current time
    @app.context_processor
    def inject_now():
        return {'now': datetime.now}

    # Inject a dummy translation function 't' into Jinja2 context
    def t(s):
        return s  # Replace with real translation logic if needed
    @app.context_processor
    def inject_t():
        return dict(t=t)

    # Register Blueprints
    try:
        from app.auth.routes import auth as auth_blueprint
        app.register_blueprint(auth_blueprint, url_prefix='/auth')
    except ImportError as e:
        print(f"⚠️  Auth blueprint not available: {e}")

    try:
        from app.routes.main import main as main_blueprint
        app.register_blueprint(main_blueprint)
    except ImportError as e:
        print(f"⚠️  Main blueprint not available: {e}")

    # Register other blueprints with error handling
    blueprint_imports = [
        ('app.routes.it_admin.routes', 'it_admin_bp', '/it-admin'),
        ('app.routes.chama', 'chama_bp', '/chama'),
        ('app.routes.elections', 'elections_bp', '/elections'),
        ('app.routes.leadership', 'leadership_bp', '/leadership'),
        ('app.routes.mpesa', 'mpesa_bp', '/mpesa'),
        ('app.routes.loans', 'loans_bp', '/loans'),
        ('app.routes.penalties', 'penalties_bp', '/penalties'),
        ('app.routes.notifications', 'notifications_bp', '/notifications'),
        ('app.routes.membership', 'membership_bp', '/membership'),
        ('app.routes.preferences', 'preferences_bp', '/preferences'),
        ('app.routes.reports', 'reports_bp', '/reports'),
        ('app.routes.integrations', 'integrations_bp', '/integrations'),
        ('app.routes.analytics', 'analytics_bp', '/analytics'),
        ('app.routes.investment', 'investment_bp', '/investment'),
        ('app.routes.subscription_new', 'subscription_new_bp', '/subscription'),
        ('app.routes.admin', 'admin_bp', '/admin'),
        ('app.routes.payments', 'payments_bp', '/payments'),
        ('app.routes.receipts', 'receipts_bp', '/receipts'),
        ('app.routes.settings', 'settings_bp', '/settings'),
        ('app.routes.compliance', 'compliance_bp', '/compliance'),
        ('app.routes.recurring', 'recurring_bp', '/recurring'),
        ('app.routes.subscription', 'subscription_bp', '/subscription_old'),
        ('app.routes.twofa', 'twofa_bp', '/twofa'),
        ('app.routes.test_features', 'test_bp', '/test'),
        ('app.routes.multisig', 'multisig_bp', '/multisig'),
        ('app.routes.minutes', 'minutes_bp', '/minutes'),
        ('app.routes.currency', 'currency_bp', '/currency'),
        ('app.routes.security_admin', 'security_admin', '/security_admin'),
        ('app.routes.api', 'api_bp', '/api'),
        ('app.routes.mobile_api', 'mobile_api_bp', '/mobile_api'),
        ('app.routes.feedback', 'feedback_bp', '/feedback'),
        ('app.routes.enterprise', 'enterprise_bp', '/enterprise'),
        ('app.routes.health', 'health_bp', '/health'),
        # New feature blueprints
        ('app.routes.marketplace', 'marketplace_bp', '/marketplace'),
        ('app.routes.lending', 'lending_bp', '/lending'),
        ('app.routes.analytics_api', 'analytics_api_bp', '/api/analytics'),
        ('app.routes.language', 'language_bp', '/language'),
        # Advanced features
        ('app.routes.ai_recommendations', 'ai_recommendations_bp', '/ai'),
        ('app.routes.chat', 'chat_bp', '/chat'),
        ('app.routes.reconciliation', 'reconciliation_bp', '/reconciliation'),
        ('app.routes.fraud_detection', 'fraud_detection_bp', '/fraud'),
        ('app.routes.identity', 'identity_bp', '/identity'),
        ('app.routes.webhooks', 'webhooks_bp', '/webhooks'),
        ('app.routes.gamification', 'gamification_bp', '/gamification'),
        ('app.routes.tax', 'tax_bp', '/tax'),
        ('app.routes.pwa', 'pwa_bp', '/pwa'),
    ]

    for module_path, blueprint_name, url_prefix in blueprint_imports:
        try:
            module = __import__(module_path, fromlist=[blueprint_name])
            blueprint = getattr(module, blueprint_name)
            app.register_blueprint(blueprint, url_prefix=url_prefix)
        except (ImportError, AttributeError) as e:
            print(f"⚠️  {blueprint_name} not available: {e}")

    return app
