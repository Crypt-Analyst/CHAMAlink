from app import db
from datetime import datetime, timedelta
from enum import Enum

class PlanType(Enum):
    BASIC = "basic"
    ADVANCED = "advanced" 
    ENTERPRISE = "enterprise"

class EnterpriseBillingType(Enum):
    FIXED = "fixed"  # Fixed monthly/yearly fee
    PER_MEMBER = "per_member"  # Per member pricing
    HYBRID = "hybrid"  # Base fee + per member

class EnterpriseSubscriptionPlan(db.Model):
    """Enhanced subscription plans with enterprise features"""
    __tablename__ = 'enterprise_subscription_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    plan_type = db.Column(db.Enum(PlanType), nullable=False)
    billing_type = db.Column(db.Enum(EnterpriseBillingType), default=EnterpriseBillingType.FIXED)
    
    # Pricing structure
    price_monthly = db.Column(db.Float, nullable=False)
    price_yearly = db.Column(db.Float)  # Optional yearly pricing
    price_per_member = db.Column(db.Float, default=0)  # Per member pricing (KES 30 for SACCO/NGO)
    base_service_fee = db.Column(db.Float, default=0)  # Base service fee (KES 1000 for SACCO/NGO)
    training_fee_per_day = db.Column(db.Float, default=0)  # Training fee (KES 500/day)
    currency = db.Column(db.String(3), default='KES')
    
    # Feature limits
    max_chamas = db.Column(db.Integer, default=1)
    max_members_per_chama = db.Column(db.Integer, default=50)
    max_loans_per_month = db.Column(db.Integer, default=10)
    max_sms_per_month = db.Column(db.Integer, default=100)
    max_file_uploads_mb = db.Column(db.Integer, default=100)
    
    # Feature flags
    has_sms_notifications = db.Column(db.Boolean, default=False)
    has_advanced_reporting = db.Column(db.Boolean, default=False)
    has_bulk_operations = db.Column(db.Boolean, default=False)
    has_api_access = db.Column(db.Boolean, default=False)
    has_white_labeling = db.Column(db.Boolean, default=False)
    has_priority_support = db.Column(db.Boolean, default=False)
    has_audit_logs = db.Column(db.Boolean, default=False)
    has_multi_signature = db.Column(db.Boolean, default=False)
    has_automated_backups = db.Column(db.Boolean, default=False)
    has_custom_branding = db.Column(db.Boolean, default=False)
    has_dedicated_manager = db.Column(db.Boolean, default=False)
    has_training_support = db.Column(db.Boolean, default=False)
    
    # Metadata
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    enterprise_subscriptions = db.relationship('EnterpriseUserSubscription', back_populates='plan', lazy=True)
    
    def get_yearly_savings(self):
        """Calculate savings when paying yearly vs monthly"""
        if self.price_yearly:
            monthly_cost = self.price_monthly * 12
            return monthly_cost - self.price_yearly
        return 0
    
    def get_feature_list(self):
        """Get list of features for this plan"""
        features = []
        
        # Special messaging for Enterprise plan (includes SACCO/NGO/Government features)
        if self.plan_type == PlanType.ENTERPRISE:
            features.extend([
                "Perfect for SACCOs, NGOs & Government",
                "Large organizations & institutions",
                f"Pay per member: KES {self.price_per_member or 30}/member/month",
                f"Monthly service fee: KES {self.base_service_fee or 1000}",
                f"Training support: KES {self.training_fee_per_day or 500}/day",
                "Scale from 1 to 10,000+ members",
                "Unlimited chamas/groups",
                "Dedicated account manager",
                "Priority enterprise support"
            ])
        else:
            # Basic features for other plans
            features.extend([
                f"Up to {self.max_chamas} chama{'s' if self.max_chamas > 1 else ''}",
                f"Up to {self.max_members_per_chama} members per chama",
                f"{self.max_loans_per_month} loans per month",
                "Basic financial tracking",
                "Member management",
                "Basic reporting"
            ])
        
        # Advanced features for all plans
        if self.has_sms_notifications:
            features.append(f"{self.max_sms_per_month} SMS notifications per month")
        
        if self.has_advanced_reporting:
            features.append("Advanced reporting & analytics")
        
        if self.has_bulk_operations:
            features.append("Bulk operations & imports")
        
        if self.has_api_access:
            features.append("API access for integrations")
        
        if self.has_white_labeling:
            features.append("White-label customization")
        
        if self.has_priority_support:
            features.append("Priority customer support")
        
        if self.has_audit_logs:
            features.append("Advanced audit logs")
        
        if self.has_multi_signature:
            features.append("Multi-signature approvals")
        
        if self.has_automated_backups:
            features.append("Automated daily backups")
        
        if self.has_custom_branding:
            features.append("Custom branding & themes")
        
        if self.has_dedicated_manager:
            features.append("Dedicated account manager")
        
        if self.has_training_support:
            features.append("Training & onboarding support")
        
        return features
    
    @staticmethod
    def create_default_plans():
        """Create default subscription plans"""
        plans = [
            {
                'name': 'Basic Plan',
                'plan_type': PlanType.BASIC,
                'price_monthly': 200.00,
                'price_yearly': 2000.00,  # 2 months free
                'max_chamas': 1,
                'max_members_per_chama': 30,
                'max_loans_per_month': 5,
                'max_sms_per_month': 50,
                'max_file_uploads_mb': 50,
                'has_sms_notifications': True,
                'description': 'Perfect for small chamas getting started with digital management'
            },
            {
                'name': 'Advanced Plan', 
                'plan_type': PlanType.ADVANCED,
                'price_monthly': 350.00,
                'price_yearly': 3500.00,  # 2 months free
                'max_chamas': 3,
                'max_members_per_chama': 100,
                'max_loans_per_month': 20,
                'max_sms_per_month': 200,
                'max_file_uploads_mb': 200,
                'has_sms_notifications': True,
                'has_advanced_reporting': True,
                'has_bulk_operations': True,
                'has_audit_logs': True,
                'has_multi_signature': True,
                'has_automated_backups': True,
                'description': 'Ideal for growing chamas and SACCO branches'
            },
            {
                'name': 'Enterprise Plan',
                'plan_type': PlanType.ENTERPRISE,
                'price_monthly': 0.00,  # Custom pricing
                'max_chamas': 999,
                'max_members_per_chama': 10000,
                'max_loans_per_month': 1000,
                'max_sms_per_month': 10000,
                'max_file_uploads_mb': 5000,
                'has_sms_notifications': True,
                'has_advanced_reporting': True,
                'has_bulk_operations': True,
                'has_api_access': True,
                'has_white_labeling': True,
                'has_priority_support': True,
                'has_audit_logs': True,
                'has_multi_signature': True,
                'has_automated_backups': True,
                'has_custom_branding': True,
                'has_dedicated_manager': True,
                'has_training_support': True,
                'description': 'Enterprise solution for SACCOs, NGOs, Government agencies, and large organizations with flexible per-member pricing'
            }
        ]
        
        for plan_data in plans:
            existing = EnterpriseSubscriptionPlan.query.filter_by(name=plan_data['name']).first()
            if not existing:
                plan = EnterpriseSubscriptionPlan(**plan_data)
                db.session.add(plan)
        
        db.session.commit()
    
    def __repr__(self):
        return f'<EnterpriseSubscriptionPlan {self.name}>'

    def calculate_monthly_cost(self, member_count=0, include_service=False, training_days=0):
        """Calculate monthly cost based on billing type and member count"""
        if self.billing_type == EnterpriseBillingType.FIXED:
            return self.price_monthly
        
        elif self.billing_type == EnterpriseBillingType.PER_MEMBER:
            # SACCO/NGO pricing: KES 30 per member
            member_cost = member_count * self.price_per_member
            service_cost = self.base_service_fee if include_service else 0
            training_cost = training_days * self.training_fee_per_day
            return member_cost + service_cost + training_cost
        
        elif self.billing_type == EnterpriseBillingType.HYBRID:
            # Base fee + per member pricing
            base_cost = self.price_monthly
            member_cost = member_count * self.price_per_member
            service_cost = self.base_service_fee if include_service else 0
            training_cost = training_days * self.training_fee_per_day
            return base_cost + member_cost + service_cost + training_cost
        
        return self.price_monthly

    def get_member_limit_for_payment(self, payment_amount):
        """Calculate how many members are allowed based on payment amount"""
        if self.billing_type == EnterpriseBillingType.PER_MEMBER and self.price_per_member > 0:
            # Subtract service fee if it was included
            remaining_amount = payment_amount - self.base_service_fee
            if remaining_amount <= 0:
                return 0
            return int(remaining_amount / self.price_per_member)
        return self.max_members_per_chama

    def can_add_member(self, current_member_count, paid_member_limit):
        """Check if organization can add another member based on their payment"""
        if self.billing_type == EnterpriseBillingType.PER_MEMBER:
            return current_member_count < paid_member_limit
        return current_member_count < self.max_members_per_chama

class EnterpriseUserSubscription(db.Model):
    """Enhanced user subscription with enterprise features"""
    __tablename__ = 'enterprise_user_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('enterprise_subscription_plans.id'), nullable=False)
    
    # Subscription details
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    auto_renew = db.Column(db.Boolean, default=True)
    
    # Payment details
    payment_method = db.Column(db.String(20), default='mpesa')  # mpesa, bank_transfer, etc.
    last_payment_date = db.Column(db.DateTime)
    next_payment_date = db.Column(db.DateTime)
    payment_frequency = db.Column(db.String(10), default='monthly')  # monthly, yearly
    
    # Usage tracking and limits
    current_chamas = db.Column(db.Integer, default=0)
    current_members = db.Column(db.Integer, default=0)
    paid_member_limit = db.Column(db.Integer, default=0)  # Members allowed based on payment
    monthly_loans = db.Column(db.Integer, default=0)
    monthly_sms_sent = db.Column(db.Integer, default=0)
    storage_used_mb = db.Column(db.Float, default=0.0)
    
    # Payment tracking for per-member billing
    last_payment_amount = db.Column(db.Float, default=0.0)
    service_fee_paid = db.Column(db.Boolean, default=False)
    training_days_purchased = db.Column(db.Integer, default=0)
    
    # Enterprise features
    custom_domain = db.Column(db.String(100))
    white_label_config = db.Column(db.JSON)
    dedicated_manager_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='enterprise_subscriptions')
    plan = db.relationship('EnterpriseSubscriptionPlan', back_populates='enterprise_subscriptions')
    payments = db.relationship('EnterpriseSubscriptionPayment', back_populates='subscription')
    dedicated_manager = db.relationship('User', foreign_keys=[dedicated_manager_id])
    
    @property
    def is_expired(self):
        """Check if subscription is expired"""
        return self.end_date and datetime.utcnow() > self.end_date
    
    @property
    def days_remaining(self):
        """Get days remaining in subscription"""
        if self.end_date:
            delta = self.end_date - datetime.utcnow()
            return max(0, delta.days)
        return 0
    
    @property
    def usage_percentage(self):
        """Get usage percentage for various limits"""
        if not self.plan:
            return {}
        
        return {
            'chamas': (self.current_chamas / max(1, self.plan.max_chamas)) * 100,
            'members': (self.current_members / max(1, self.plan.max_members_per_chama)) * 100,
            'loans': (self.monthly_loans / max(1, self.plan.max_loans_per_month)) * 100,
            'sms': (self.monthly_sms_sent / max(1, self.plan.max_sms_per_month)) * 100,
            'storage': (self.storage_used_mb / max(1, self.plan.max_file_uploads_mb)) * 100
        }
    
    def can_create_chama(self):
        """Check if user can create another chama"""
        return self.current_chamas < self.plan.max_chamas
    
    def can_add_member(self, chama_id):
        """Check if user can add another member to a chama"""
        from app.models.chama import Chama
        chama = Chama.query.get(chama_id)
        if chama:
            return len(chama.members) < self.plan.max_members_per_chama
        return False
    
    def can_send_sms(self):
        """Check if user can send another SMS"""
        return self.monthly_sms_sent < self.plan.max_sms_per_month
    
    def can_create_loan(self):
        """Check if user can create another loan this month"""
        return self.monthly_loans < self.plan.max_loans_per_month
    
    def reset_monthly_usage(self):
        """Reset monthly usage counters"""
        self.monthly_loans = 0
        self.monthly_sms_sent = 0
        db.session.commit()
    
    def extend_subscription(self, months=1):
        """Extend subscription by specified months"""
        if not self.end_date:
            self.end_date = datetime.utcnow()
        
        self.end_date += timedelta(days=30 * months)
        self.next_payment_date = self.end_date
        db.session.commit()
    
    def __repr__(self):
        return f'<EnterpriseUserSubscription {self.user.username} - {self.plan.name}>'

class EnterpriseSubscriptionPayment(db.Model):
    """Track subscription payments"""
    __tablename__ = 'enterprise_subscription_payments'
    
    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('enterprise_user_subscriptions.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='KES')
    payment_method = db.Column(db.String(20), default='mpesa')
    transaction_id = db.Column(db.String(100))
    payment_reference = db.Column(db.String(100))
    
    # Payment status
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed, refunded
    paid_at = db.Column(db.DateTime)
    
    # Period covered by this payment
    period_start = db.Column(db.DateTime)
    period_end = db.Column(db.DateTime)
    
    # Invoice details
    invoice_number = db.Column(db.String(50))
    invoice_generated = db.Column(db.Boolean, default=False)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscription = db.relationship('EnterpriseUserSubscription', back_populates='payments')
    
    def generate_invoice_number(self):
        """Generate invoice number"""
        if not self.invoice_number:
            self.invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{self.id:06d}"
            db.session.commit()
        return self.invoice_number
    
    def __repr__(self):
        return f'<EnterpriseSubscriptionPayment {self.amount} {self.currency} - {self.status}>'

class BankTransferPayment(db.Model):
    """Bank transfer payment records for manual verification"""
    __tablename__ = 'bank_transfer_payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'), nullable=False)
    pricing_id = db.Column(db.Integer, db.ForeignKey('subscription_plan_pricing.id'), nullable=False)
    
    # Transfer details
    amount = db.Column(db.Float, nullable=False)
    transfer_reference = db.Column(db.String(100), nullable=False)
    transfer_date = db.Column(db.Date, nullable=False)
    sender_name = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text)
    
    # Bank details
    bank_name = db.Column(db.String(50), default='Cooperative Bank')
    account_number = db.Column(db.String(50), default='01116844755200')
    paybill = db.Column(db.String(20), default='400200')
    
    # Verification status
    status = db.Column(db.String(30), default='pending_verification')  # pending_verification, verified, rejected
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    verified_at = db.Column(db.DateTime)
    admin_notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], back_populates='bank_transfers')
    plan = db.relationship('SubscriptionPlan', backref='bank_transfers')
    pricing = db.relationship('SubscriptionPlanPricing', backref='bank_transfers')
    verified_by_user = db.relationship('User', foreign_keys=[verified_by])
    
    def __repr__(self):
        return f'<BankTransferPayment {self.amount} KES - {self.status}>'
