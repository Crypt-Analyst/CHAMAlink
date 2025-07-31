import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Force reload for blueprint registration
print("🔄 Loading blueprints...")

# Get database URL - prioritize SQLALCHEMY_DATABASE_URI
database_url = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
if database_url:
    os.environ["SQLALCHEMY_DATABASE_URI"] = database_url
    print("✅ Database URL loaded successfully")
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
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "chamalink-secret-key")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    # Session configuration
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes

    # Email configuration
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
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

    # Template context processor
    @app.context_processor
    def inject_now():
        return {'now': datetime.now}

    # Register Blueprints
    try:
        from app.auth.routes import auth as auth_blueprint
        app.register_blueprint(auth_blueprint, url_prefix='/auth')
        print("✅ Auth blueprint registered")
    except ImportError as e:
        print(f"⚠️  Auth blueprint not available: {e}")

    try:
        from app.routes.main import main as main_blueprint
        app.register_blueprint(main_blueprint)
        print("✅ Main blueprint registered")
    except ImportError as e:
        print(f"⚠️  Main blueprint not available: {e}")

    # Register other blueprints with error handling
    blueprint_imports = [
        ('app.routes.chama', 'chama_bp', '/chama'),
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
    ]

    for module_path, blueprint_name, url_prefix in blueprint_imports:
        try:
            module = __import__(module_path, fromlist=[blueprint_name])
            blueprint = getattr(module, blueprint_name)
            app.register_blueprint(blueprint, url_prefix=url_prefix)
            print(f"✅ {blueprint_name} registered")
        except (ImportError, AttributeError) as e:
            print(f"⚠️  {blueprint_name} not available: {e}")

    return app
