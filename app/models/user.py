from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='member')
    is_super_admin = db.Column(db.Boolean, default=False)
    
    # Personal Information
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    date_of_birth = db.Column(db.Date)
    national_id = db.Column(db.String(20), unique=True)
    passport_number = db.Column(db.String(20), unique=True)
    
    # Account Security
    is_email_verified = db.Column(db.Boolean, default=False)
    is_documents_verified = db.Column(db.Boolean, default=False)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    
    # Password Reset
    password_reset_token = db.Column(db.String(100), unique=True)
    password_reset_expires = db.Column(db.DateTime)
    
    # Guardian Information (for users under 18)
    is_minor = db.Column(db.Boolean, default=False)
    guardian_name = db.Column(db.String(100))
    guardian_phone = db.Column(db.String(20))
    guardian_id = db.Column(db.String(20))
    guardian_relationship = db.Column(db.String(50))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # User Preferences
    preferred_language = db.Column(db.String(5), default='en')
    preferred_theme = db.Column(db.String(20), default='light')
    preferred_font = db.Column(db.String(20), default='default')
    preferred_currency = db.Column(db.String(3), default='KES')  # ISO currency code
    
    # Location Information
    country_code = db.Column(db.String(2))  # ISO country code
    country_name = db.Column(db.String(100))
    city = db.Column(db.String(100))
    timezone = db.Column(db.String(50), default='Africa/Nairobi')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_chama_admin(self, chama_id):
        """Check if user is admin of a specific chama"""
        from app.models.chama import chama_members
        membership = db.session.query(chama_members).filter(
            chama_members.c.user_id == self.id,
            chama_members.c.chama_id == chama_id,
            chama_members.c.role.in_(['admin', 'creator'])
        ).first()
        return membership is not None
    
    def get_chama_role(self, chama_id):
        """Get user's role in a specific chama"""
        from app.models.chama import chama_members
        membership = db.session.query(chama_members).filter(
            chama_members.c.user_id == self.id,
            chama_members.c.chama_id == chama_id
        ).first()
        return membership.role if membership else None
    
    def has_pending_loans(self, chama_id=None):
        """Check if user has pending loans"""
        from app.models.chama import LoanApplication
        query = LoanApplication.query.filter_by(user_id=self.id, status='pending')
        if chama_id:
            query = query.filter_by(chama_id=chama_id)
        return query.first() is not None
    
    def get_total_contributions(self, chama_id):
        """Get total contributions by user to a specific chama"""
        from app.models.chama import Transaction
        total = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == self.id,
            Transaction.chama_id == chama_id,
            Transaction.type == 'contribution'
        ).scalar()
        return total or 0.0
    
    def get_unread_notifications_count(self):
        """Get count of unread notifications"""
        from app.models.chama import Notification
        return Notification.query.filter_by(user_id=self.id, is_read=False).count()

    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    @property
    def is_account_locked(self):
        return self.locked_until and datetime.utcnow() < self.locked_until
    
    # Relationships
    bank_transfers = db.relationship('BankTransferPayment', foreign_keys='BankTransferPayment.user_id', 
                                   back_populates='user', lazy='dynamic')
    
    @property
    def chamas(self):
        """Property to get all chamas this user is a member of"""
        return self.get_chamas()

    def get_chamas(self):
        """Get all chamas this user is a member of"""
        from app.models.chama import Chama, chama_members
        return db.session.query(Chama).join(chama_members).filter(
            chama_members.c.user_id == self.id
        ).all()
    
    def is_member_of_chama(self, chama_id):
        """Check if user is a member of a specific chama"""
        from app.models.chama import chama_members
        membership = db.session.query(chama_members).filter(
            chama_members.c.user_id == self.id,
            chama_members.c.chama_id == chama_id
        ).first()
        return membership is not None
    
    # Flask-Login required properties
    def get_id(self):
        """Return the user ID as a string"""
        return str(self.id)
    
    @property
    def is_authenticated(self):
        """User is authenticated if they have a valid ID"""
        return True
    
    @property  
    def is_anonymous(self):
        """User is not anonymous"""
        return False
    
    # Override Flask-Login's is_active to use our database field
    # Note: This ensures Flask-Login respects our is_active field
    # UserMixin provides a default is_active that returns True
    
    # ...existing code...

    @property
    def current_subscription(self):
        from app.models.subscription import UserSubscription
        return UserSubscription.query.filter_by(
            user_id=self.id
        ).filter(
            UserSubscription.status.in_(['trial', 'active'])
        ).order_by(UserSubscription.end_date.desc()).first()
    
    @property
    def is_adult(self):
        if self.date_of_birth:
            age = (datetime.now().date() - self.date_of_birth).days / 365.25
            return age >= 18
        return not self.is_minor
    
    def can_access_feature(self, feature_name):
        """Check if user's subscription allows access to a feature"""
        subscription = self.current_subscription
        if not subscription or not subscription.is_active:
            return False
        
        plan_features = subscription.plan.features or {}
        return plan_features.get(feature_name, False)
    
    def get_chama_limit(self):
        """Get maximum number of chamas user can create/join"""
        subscription = self.current_subscription
        if not subscription or not subscription.is_active:
            return 0
        return subscription.plan.max_chamas
    
    def get_membership_duration(self, chama_id):
        """Get how long user has been a member of a chama (in days)"""
        from app.models.chama import chama_members
        membership = db.session.query(chama_members.c.joined_at).filter(
            chama_members.c.user_id == self.id,
            chama_members.c.chama_id == chama_id
        ).first()
        
        if membership and membership[0]:
            return (datetime.utcnow() - membership[0]).days
        return 0
    
    def increment_failed_login(self):
        """Increment failed login attempts and lock account if necessary"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 3:
            # Lock account for 24 hours
            from datetime import timedelta
            self.locked_until = datetime.utcnow() + timedelta(hours=24)
        db.session.commit()
    
    def reset_failed_login(self):
        """Reset failed login attempts on successful login"""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def generate_password_reset_token(self):
        """Generate a password reset token"""
        import secrets
        from datetime import timedelta
        
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
        db.session.commit()
        return self.password_reset_token
    
    def verify_password_reset_token(self, token):
        """Verify if the password reset token is valid"""
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        
        if datetime.utcnow() > self.password_reset_expires:
            return False
            
        return self.password_reset_token == token
    
    def clear_password_reset_token(self):
        """Clear password reset token after use"""
        self.password_reset_token = None
        self.password_reset_expires = None
        db.session.commit()
    
    def member_since(self, chama_id):
        """Get the date when user joined a specific chama"""
        from app.models.chama import chama_members
        membership = db.session.query(chama_members).filter(
            chama_members.c.user_id == self.id,
            chama_members.c.chama_id == chama_id
        ).first()
        return membership.joined_at if membership and hasattr(membership, 'joined_at') else self.created_at

    @property
    def is_verified(self):
        """Check if user is verified (email verified)"""
        return self.is_email_verified

    def __repr__(self):
        return f'<User {self.username}>'
