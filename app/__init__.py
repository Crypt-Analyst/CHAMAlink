import os
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from dotenv import load_dotenv

# ✅ Load environment variables from .env
load_dotenv()

# 🧠 Initialize core Flask extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()

print("DB URI:", os.getenv("DATABASE_URL"))

def create_app():
    app = Flask(__name__)

    # 🔐 Configuration
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "chamalink-secret-key")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TEMPLATES_AUTO_RELOAD'] = True  # Force template reloading
    
    # Session configuration for better login persistence
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes

    # 📧 Email configuration
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@chamalink.com')

    # 📦 Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    login_manager.session_protection = 'strong'  # Better session protection

    # 👤 Load user model
    from .models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # 🕐 Template context processor to make datetime available in templates
    @app.context_processor
    def inject_now():
        return {'now': datetime.now}

    # 🔗 Register Blueprints
    from app.auth.routes import auth as auth_blueprint
    from app.routes.main import main as main_blueprint
    from app.routes.chama import chama_bp
    from app.routes.mpesa import mpesa_bp
    from app.routes.loans import loans_bp
    from app.routes.penalties import penalties_bp
    from app.routes.notifications import notifications_bp
    from app.routes.settings import settings_bp
    from app.routes.membership import membership_bp
    from app.routes.subscription import subscription_bp
    from app.routes.subscription_new import subscription_new_bp
    from app.routes.multisig import multisig_bp
    from app.routes.twofa import twofa_bp
    from app.routes.reports import reports_bp
    from app.routes.receipts import receipts_bp
    from app.routes.recurring import recurring_bp
    from app.routes.minutes import minutes_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp
    from app.routes.enterprise import enterprise_bp

    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(main_blueprint)
    app.register_blueprint(chama_bp)
    app.register_blueprint(mpesa_bp)
    app.register_blueprint(loans_bp)
    app.register_blueprint(penalties_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(membership_bp)
    app.register_blueprint(subscription_bp, url_prefix='/subscription')
    app.register_blueprint(subscription_new_bp, url_prefix='/plans')
    app.register_blueprint(multisig_bp, url_prefix='/multisig')
    app.register_blueprint(twofa_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(receipts_bp)
    app.register_blueprint(recurring_bp)
    app.register_blueprint(minutes_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(enterprise_bp, url_prefix='/enterprise')

    return app
