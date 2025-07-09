from app import db
from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import UUID
import uuid

class SubscriptionPlan(db.Model):
    __tablename__ = 'subscription_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)  # 'basic', 'advanced'
    price = db.Column(db.Float, nullable=False)
    max_chamas = db.Column(db.Integer, nullable=False)
    features = db.Column(db.JSON)  # Store features as JSON
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SubscriptionPlan {self.name}>'

class UserSubscription(db.Model):
    __tablename__ = 'user_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'), nullable=False)
    status = db.Column(db.String(20), default='trial')  # trial, active, expired, cancelled
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    trial_end_date = db.Column(db.DateTime)
    is_trial = db.Column(db.Boolean, default=True)
    auto_renew = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='subscriptions')
    plan = db.relationship('SubscriptionPlan', backref='subscriptions')
    
    @property
    def is_active(self):
        return self.status in ['trial', 'active'] and self.end_date > datetime.utcnow()
    
    @property
    def days_remaining(self):
        if self.end_date > datetime.utcnow():
            return (self.end_date - datetime.utcnow()).days
        return 0
    
    @property
    def is_trial_active(self):
        return self.is_trial and self.trial_end_date and self.trial_end_date > datetime.utcnow()
    
    def __repr__(self):
        return f'<UserSubscription {self.user.username} - {self.plan.name}>'

class SubscriptionPlanPricing(db.Model):
    __tablename__ = 'subscription_plan_pricing'
    
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'), nullable=False)
    months = db.Column(db.Integer, nullable=False)  # 1, 3, 6, 12
    price_per_month = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    bonus_months = db.Column(db.Integer, default=0)  # Extra months for bulk purchases
    discount_percentage = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    plan = db.relationship('SubscriptionPlan', backref='pricing_options')
    
    @property
    def total_months_provided(self):
        """Total months user gets (paid months + bonus months)"""
        return self.months + self.bonus_months
    
    @property
    def savings_amount(self):
        """How much user saves compared to monthly payments"""
        monthly_price = self.plan.price
        full_monthly_cost = monthly_price * self.months
        return full_monthly_cost - self.total_price
    
    def __repr__(self):
        return f'<PlanPricing {self.plan.name} - {self.months}mo>'

class SubscriptionPayment(db.Model):
    __tablename__ = 'subscription_payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('user_subscriptions.id'), nullable=False)
    pricing_id = db.Column(db.Integer, db.ForeignKey('subscription_plan_pricing.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    months_purchased = db.Column(db.Integer, default=1)
    bonus_months = db.Column(db.Integer, default=0)
    mpesa_receipt_number = db.Column(db.String(200))
    payment_status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    payment_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='subscription_payments')
    subscription = db.relationship('UserSubscription', backref='payments')
    pricing = db.relationship('SubscriptionPlanPricing', backref='payments')
    
    @property
    def total_months_provided(self):
        return self.months_purchased + self.bonus_months
    
    def __repr__(self):
        return f'<SubscriptionPayment {self.id}>'

class UserDocument(db.Model):
    __tablename__ = 'user_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # 'id', 'passport', 'photo'
    file_path = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(200), nullable=False)
    verification_status = db.Column(db.String(20), default='pending')  # pending, verified, rejected
    verification_notes = db.Column(db.Text)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='documents')
    verifier = db.relationship('User', foreign_keys=[verified_by])
    
    def __repr__(self):
        return f'<UserDocument {self.user.username} - {self.document_type}>'

class LoginAttempt(db.Model):
    __tablename__ = 'login_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    email = db.Column(db.String(120))  # Store email even if user doesn't exist
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    success = db.Column(db.Boolean, default=False)
    attempt_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='login_attempts')
    
    def __repr__(self):
        return f'<LoginAttempt {self.email} - {self.success}>'

class EmailVerification(db.Model):
    __tablename__ = 'email_verifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    verification_token = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref='email_verifications')
    
    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f'<EmailVerification {self.email}>'

class LoanApprovalToken(db.Model):
    __tablename__ = 'loan_approval_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    loan_application_id = db.Column(db.Integer, db.ForeignKey('loan_applications.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    loan_application = db.relationship('LoanApplication', backref='approval_tokens')
    admin = db.relationship('User', backref='loan_approval_tokens')
    
    @property
    def is_valid(self):
        return not self.is_used and datetime.utcnow() < self.expires_at
    
    def __repr__(self):
        return f'<LoanApprovalToken {self.token}>'

class TwoFactorAuth(db.Model):
    __tablename__ = 'two_factor_auth'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    secret_key = db.Column(db.String(100))  # For TOTP apps like Google Authenticator
    sms_enabled = db.Column(db.Boolean, default=False)
    email_enabled = db.Column(db.Boolean, default=False)
    totp_enabled = db.Column(db.Boolean, default=False)
    backup_codes = db.Column(db.JSON)  # Array of backup codes
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='two_factor_auth')
    
    def __repr__(self):
        return f'<TwoFactorAuth {self.user.username}>'

class TwoFactorCode(db.Model):
    __tablename__ = 'two_factor_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    code = db.Column(db.String(10), nullable=False)
    code_type = db.Column(db.String(20), nullable=False)  # sms, email, totp
    is_used = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='two_factor_codes')
    
    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f'<TwoFactorCode {self.user.username} - {self.code_type}>'
