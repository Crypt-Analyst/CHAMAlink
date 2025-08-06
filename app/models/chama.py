from app import db
from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
import uuid

class Chama(db.Model):
    __tablename__ = 'chamas'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    goal = db.Column(db.Text)
    monthly_contribution = db.Column(db.Float, default=0.0)
    registration_fee = db.Column(db.Float, default=0.0)  # Registration fee for new members
    total_balance = db.Column(db.Float, default=0.0)
    meeting_day = db.Column(db.String(20))  # monday, tuesday, etc.
    meeting_time = db.Column(db.Time)
    next_meeting_date = db.Column(db.DateTime)  # Next scheduled meeting
    status = db.Column(db.String(20), default='active')  # active, inactive, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    creator = db.relationship('User', backref='created_chamas')
    
    # Currency relationship
    default_currency_id = db.Column(db.Integer, db.ForeignKey('currencies.id'), nullable=True)
    
    # Many-to-many relationship with users
    members = db.relationship('User', secondary='chama_members', backref='chamas')
    
    # Currency settings
    base_currency = db.Column(db.String(3), default='KES')  # Chama's base currency
    multi_currency_enabled = db.Column(db.Boolean, default=False)  # Allow multiple currencies
    
    def __repr__(self):
        return f'<Chama {self.name}>'
    
    @property
    def member_count(self):
        return len(self.members)
    
    @property
    def formatted_balance(self):
        return f"KES {self.total_balance:,.0f}"
    
    @property
    def formatted_contribution(self):
        return f"KES {self.monthly_contribution:,.0f}"
    
    @property
    def formatted_registration_fee(self):
        return f"KES {self.registration_fee:,.0f}"
    
    @property
    def is_meeting_day(self):
        """Check if today is a meeting day"""
        if not self.meeting_day:
            return False
        today = datetime.now().strftime('%A').lower()
        return today == self.meeting_day.lower()
    
    @property
    def can_approve_today(self):
        """Check if members can be approved today (meeting day)"""
        return self.is_meeting_day
    
    @property
    def admins(self):
        """Get all admins of this chama"""
        from app.models.user import User
        return db.session.query(User).join(chama_members).filter(
            chama_members.c.chama_id == self.id,
            chama_members.c.role.in_(['admin', 'creator'])
        ).all()
    
    @property
    def regular_members(self):
        """Get all regular members (non-admin) of this chama"""
        from app.models.user import User
        return db.session.query(User).join(chama_members).filter(
            chama_members.c.chama_id == self.id,
            chama_members.c.role == 'member'
        ).all()
    
    def is_admin(self, user_id):
        """Check if user is an admin of this chama"""
        membership = db.session.query(chama_members).filter(
            chama_members.c.user_id == user_id,
            chama_members.c.chama_id == self.id,
            chama_members.c.role.in_(['admin', 'creator'])
        ).first()
        return membership is not None
    
    def can_remove_member(self, admin_user_id, target_user_id):
        """Check if admin can remove a specific member"""
        # Admin can't remove themselves
        if admin_user_id == target_user_id:
            return False
        
        # Admin can't remove the creator
        if target_user_id == self.creator_id:
            return False
        
        # Check if user is admin
        return self.is_admin(admin_user_id)
    
    def add_member(self, user_id, role='member'):
        """Add a member to the chama"""
        # Check if user is already a member
        existing = db.session.query(chama_members).filter(
            chama_members.c.user_id == user_id,
            chama_members.c.chama_id == self.id
        ).first()
        
        if existing:
            return False, "User is already a member of this chama"
        
        # Add member
        stmt = chama_members.insert().values(
            user_id=user_id,
            chama_id=self.id,
            role=role,
            joined_at=datetime.utcnow()
        )
        db.session.execute(stmt)
        return True, "Member added successfully"
    
    def remove_member(self, user_id):
        """Remove a member from the chama"""
        # Can't remove creator
        if user_id == self.creator_id:
            return False, "Cannot remove chama creator"
        
        # Remove member
        stmt = chama_members.delete().where(
            chama_members.c.user_id == user_id,
            chama_members.c.chama_id == self.id
        )
        result = db.session.execute(stmt)
        
        if result.rowcount > 0:
            return True, "Member removed successfully"
        else:
            return False, "Member not found in this chama"

# Association table for many-to-many relationship between users and chamas
chama_members = db.Table('chama_members',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('chama_id', db.Integer, db.ForeignKey('chamas.id'), primary_key=True),
    db.Column('role', db.String(20), default='member'),  # member, admin, treasurer
    db.Column('joined_at', db.DateTime, default=datetime.utcnow)
)

class ChamaMember:
    """Helper class to work with chama membership"""
    
    @staticmethod
    def get_member_role(user_id, chama_id):
        """Get member role in a chama"""
        membership = db.session.query(chama_members).filter(
            chama_members.c.user_id == user_id,
            chama_members.c.chama_id == chama_id
        ).first()
        
        if membership:
            return membership.role
        return None
    
    @staticmethod
    def get_chama_members(chama_id):
        """Get all members of a chama with their roles"""
        from app.models.user import User
        
        members = db.session.query(User, chama_members.c.role, chama_members.c.joined_at).join(
            chama_members, User.id == chama_members.c.user_id
        ).filter(chama_members.c.chama_id == chama_id).all()
        
        return [{'user': member[0], 'role': member[1], 'joined_at': member[2]} for member in members]

class Contribution(db.Model):
    """Model for tracking contributions to chamas"""
    __tablename__ = 'contributions'
    
    id = db.Column(db.Integer, primary_key=True)
    chama_id = db.Column(db.Integer, db.ForeignKey('chamas.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # contribution, shares, loan_repayment, etc.
    description = db.Column(db.Text)
    transaction_id = db.Column(db.String(100))  # M-Pesa transaction ID
    payment_method = db.Column(db.String(20), default='mpesa')  # mpesa, bank_transfer, cash
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)
    
    # Relationships
    chama = db.relationship('Chama', backref='contributions')
    user = db.relationship('User', backref='contributions')
    
    # Currency fields
    currency = db.Column(db.String(3), default='KES')  # ISO currency code
    exchange_rate = db.Column(db.Float, default=1.0)  # Rate at time of transaction
    original_amount = db.Column(db.Float)  # Amount in original currency
    
    def __repr__(self):
        return f'<Contribution {self.user.username} - {self.amount} to {self.chama.name}>'

class Loan(db.Model):
    """Model for tracking loans within chamas"""
    __tablename__ = 'loans'
    
    id = db.Column(db.Integer, primary_key=True)
    chama_id = db.Column(db.Integer, db.ForeignKey('chamas.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, default=0.0)
    purpose = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, approved, awaiting_signatures, disbursed, repaid
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    due_date = db.Column(db.DateTime)
    
    # Multi-signature support
    requires_multi_signature = db.Column(db.Boolean, default=True)  # For loans above threshold
    multi_sig_transaction_id = db.Column(db.Integer, db.ForeignKey('multi_signature_transactions.id'))
    disbursement_method = db.Column(db.String(20), default='mpesa')  # mpesa, bank_transfer, cash
    disbursement_details = db.Column(db.JSON)  # Store account/phone details
    
    # Relationships
    chama = db.relationship('Chama', backref='loans')
    user = db.relationship('User', backref='loans')
    multi_sig_transaction = db.relationship('MultiSignatureTransaction', backref='related_loans')
    
    # Currency fields
    currency = db.Column(db.String(3), default='KES')  # ISO currency code
    exchange_rate = db.Column(db.Float, default=1.0)  # Rate at time of loan
    
    @property
    def total_amount_due(self):
        """Calculate total amount due including interest"""
        return self.amount * (1 + self.interest_rate / 100)
    
    @property
    def requires_signatures(self):
        """Check if loan amount requires multi-signature approval"""
        # Loans above KES 10,000 require multi-signature by default
        return self.amount >= 10000.0 or self.requires_multi_signature
    
    def create_disbursement_transaction(self, requested_by_id, ip_address=None):
        """Create multi-signature transaction for loan disbursement"""
        if not self.requires_signatures:
            return None
        
        if self.status != 'approved':
            return None
        
        transaction = MultiSignatureTransaction.create_loan_disbursement_transaction(
            chama_id=self.chama_id,
            loan_id=self.id,
            amount=self.amount,
            requested_by_id=requested_by_id,
            ip_address=ip_address
        )
        
        db.session.add(transaction)
        db.session.flush()  # Get the ID
        
        self.multi_sig_transaction_id = transaction.id
        self.status = 'awaiting_signatures'
        
        return transaction
    
    def can_be_disbursed(self):
        """Check if loan can be disbursed"""
        if not self.requires_signatures:
            return self.status == 'approved'
        
        return (self.status == 'awaiting_signatures' and 
                self.multi_sig_transaction and 
                self.multi_sig_transaction.can_be_executed)
    
    def __repr__(self):
        return f'<Loan {self.user.username} - {self.amount} from {self.chama.name}>'

class LoanPayment(db.Model):
    """Model for tracking loan payments"""
    __tablename__ = 'loan_payments'
    
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_id = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending')
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    loan = db.relationship('Loan', backref='payments')
    
    # Currency fields
    currency = db.Column(db.String(3), default='KES')  # ISO currency code
    exchange_rate = db.Column(db.Float, default=1.0)  # Rate at time of payment
    
    def __repr__(self):
        return f'<LoanPayment {self.amount} for loan {self.loan_id}>'

class PenaltyPayment(db.Model):
    """Model for tracking penalty payments"""
    __tablename__ = 'penalty_payments'
    
    id = db.Column(db.Integer, primary_key=True)
    penalty_id = db.Column(db.Integer, db.ForeignKey('penalties.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_id = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending')
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    penalty = db.relationship('Penalty', backref='payments')
    
    # Currency fields
    currency = db.Column(db.String(3), default='KES')  # ISO currency code
    exchange_rate = db.Column(db.Float, default=1.0)  # Rate at time of payment
    
    def __repr__(self):
        return f'<PenaltyPayment {self.amount} for penalty {self.penalty_id}>'

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # contribution, withdrawal, loan, investment
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='completed')  # pending, completed, failed
    payment_method = db.Column(db.String(20), default='mpesa')  # mpesa, bank_transfer, cash
    transaction_id = db.Column(db.String(100))  # M-Pesa receipt or bank reference
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chama_id = db.Column(db.Integer, db.ForeignKey('chamas.id'), nullable=False)
    currency_id = db.Column(db.Integer, db.ForeignKey('currencies.id'), nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='transactions')
    chama = db.relationship('Chama', backref='transactions')
    
    # Currency fields
    currency = db.Column(db.String(3), default='KES')  # ISO currency code
    exchange_rate = db.Column(db.Float, default=1.0)  # Rate at time of transaction
    original_amount = db.Column(db.Float)  # Amount in original currency
    
    def __repr__(self):
        return f'<Transaction {self.type}: {self.amount}>'
    
    @property
    def formatted_amount(self):
        sign = '+' if self.type in ['contribution', 'loan_repayment'] else '-'
        return f"{sign}KES {self.amount:,.0f}"
    
    @property
    def display_title(self):
        titles = {
            'contribution': 'Monthly Contribution',
            'withdrawal': 'Withdrawal',
            'loan': 'Loan Disbursement',
            'investment': 'Investment Purchase',
            'loan_repayment': 'Loan Repayment'
        }
        return titles.get(self.type, self.type.title())

class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.Date, nullable=False)
    event_time = db.Column(db.Time)
    location = db.Column(db.String(200))
    type = db.Column(db.String(50), default='meeting')  # meeting, deadline, event
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    chama_id = db.Column(db.Integer, db.ForeignKey('chamas.id'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    chama = db.relationship('Chama', backref='events')
    creator = db.relationship('User', backref='created_events')
    
    def __repr__(self):
        return f'<Event {self.title}>'
    
    @property
    def formatted_date(self):
        return self.event_date.strftime('%d %b')
    
    @property
    def formatted_time(self):
        if self.event_time:
            return self.event_time.strftime('%I:%M %p')
        return 'All day'

class LoanApplication(db.Model):
    __tablename__ = 'loan_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    purpose = db.Column(db.Text, nullable=False)
    repayment_period = db.Column(db.Integer, nullable=False)  # months
    interest_rate = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, disbursed
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    approval_date = db.Column(db.DateTime)
    disbursement_date = db.Column(db.DateTime)
    due_date = db.Column(db.DateTime)
    amount_paid = db.Column(db.Float, default=0.0)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chama_id = db.Column(db.Integer, db.ForeignKey('chamas.id'), nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='loan_applications')
    chama = db.relationship('Chama', backref='loan_applications')
    approvals = db.relationship('LoanApproval', backref='loan_application', cascade='all, delete-orphan')
    
    # Currency fields
    currency = db.Column(db.String(3), default='KES')  # ISO currency code
    exchange_rate = db.Column(db.Float, default=1.0)  # Rate at time of application
    
    @property
    def formatted_amount(self):
        return f"KES {self.amount:,.0f}"
    
    @hybrid_property
    def remaining_amount(self):
        return self.amount - self.amount_paid
    
    @remaining_amount.expression
    def remaining_amount(cls):
        return cls.amount - cls.amount_paid
    
    @property
    def is_overdue(self):
        return self.due_date and datetime.utcnow() > self.due_date and self.remaining_amount > 0
    
    @property
    def approval_count(self):
        return len([a for a in self.approvals if a.status == 'approved'])
    
    def __repr__(self):
        return f'<LoanApplication {self.id}: {self.amount}>'

class LoanApproval(db.Model):
    __tablename__ = 'loan_approvals'
    
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=False)  # approved, rejected
    comments = db.Column(db.Text)
    approval_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    loan_application_id = db.Column(db.Integer, db.ForeignKey('loan_applications.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    admin = db.relationship('User', backref='loan_approvals')
    
    def __repr__(self):
        return f'<LoanApproval {self.id}: {self.status}>'

class Penalty(db.Model):
    __tablename__ = 'penalties'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # late_payment, missed_meeting, etc.
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, paid
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    paid_date = db.Column(db.DateTime)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chama_id = db.Column(db.Integer, db.ForeignKey('chamas.id'), nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='penalties')
    chama = db.relationship('Chama', backref='penalties')
    
    # Currency fields
    currency = db.Column(db.String(3), default='KES')  # ISO currency code
    exchange_rate = db.Column(db.Float, default=1.0)  # Rate at time of penalty
    
    @property
    def formatted_amount(self):
        return f"KES {self.amount:,.0f}"
    
    def __repr__(self):
        return f'<Penalty {self.id}: {self.type}>'

class ChamaMembershipRequest(db.Model):
    __tablename__ = 'chama_membership_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    request_type = db.Column(db.String(20), nullable=False)  # join, leave
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    reason = db.Column(db.Text)
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    decision_date = db.Column(db.DateTime)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chama_id = db.Column(db.Integer, db.ForeignKey('chamas.id'), nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='membership_requests')
    chama = db.relationship('Chama', backref='membership_requests')
    approvals = db.relationship('MembershipApproval', backref='membership_request', cascade='all, delete-orphan')
    
    @property
    def approval_count(self):
        return len([a for a in self.approvals if a.status == 'approved'])
    
    def __repr__(self):
        return f'<ChamaMembershipRequest {self.id}: {self.request_type}>'

class MembershipApproval(db.Model):
    __tablename__ = 'membership_approvals'
    
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=False)  # approved, rejected
    comments = db.Column(db.Text)
    approval_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    membership_request_id = db.Column(db.Integer, db.ForeignKey('chama_membership_requests.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    admin = db.relationship('User', backref='membership_approvals')
    
    def __repr__(self):
        return f'<MembershipApproval {self.id}: {self.status}>'

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # meeting, loan, penalty, etc.
    is_read = db.Column(db.Boolean, default=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    related_id = db.Column(db.Integer)  # ID of related entity (minutes, announcement, etc.)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chama_id = db.Column(db.Integer, db.ForeignKey('chamas.id'))
    
    # Relationships
    user = db.relationship('User', backref='notifications')
    chama = db.relationship('Chama', backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.title}>'

class MpesaTransaction(db.Model):
    __tablename__ = 'mpesa_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    checkout_request_id = db.Column(db.String(200), unique=True)
    merchant_request_id = db.Column(db.String(200))
    amount = db.Column(db.Float, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    account_reference = db.Column(db.String(200))
    transaction_desc = db.Column(db.Text)
    mpesa_receipt_number = db.Column(db.String(200))
    transaction_date = db.Column(db.DateTime)
    result_code = db.Column(db.String(10))
    result_desc = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chama_id = db.Column(db.Integer, db.ForeignKey('chamas.id'))
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'))
    
    # Relationships
    user = db.relationship('User', backref='mpesa_transactions')
    chama = db.relationship('Chama', backref='mpesa_transactions')
    transaction = db.relationship('Transaction', backref='mpesa_transaction')
    
    def __repr__(self):
        return f'<MpesaTransaction {self.id}: {self.amount}>'

class RegistrationFeePayment(db.Model):
    __tablename__ = 'registration_fee_payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chama_id = db.Column(db.Integer, db.ForeignKey('chamas.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    mpesa_receipt_number = db.Column(db.String(200))
    payment_status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    payment_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='registration_fee_payments')
    chama = db.relationship('Chama', backref='registration_fee_payments')
    
    def __repr__(self):
        return f'<RegistrationFeePayment {self.user.username} - {self.chama.name}>'

class ManualPaymentVerification(db.Model):
    __tablename__ = 'manual_payment_verifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chama_id = db.Column(db.Integer, db.ForeignKey('chamas.id'))
    payment_type = db.Column(db.String(50), nullable=False)  # contribution, loan_repayment, penalty, registration_fee
    amount = db.Column(db.Float, nullable=False)
    mpesa_message = db.Column(db.Text, nullable=False)  # Full M-Pesa message
    transaction_id = db.Column(db.String(100))  # Extracted transaction ID
    verification_status = db.Column(db.String(20), default='pending')  # pending, verified, rejected
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    verification_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='payment_verifications')
    verifier = db.relationship('User', foreign_keys=[verified_by])
    chama = db.relationship('Chama', backref='payment_verifications')
    
    def __repr__(self):
        return f'<ManualPaymentVerification {self.user.username} - {self.amount}>'



class Receipt(db.Model):
    __tablename__ = 'receipts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chama_id = db.Column(db.Integer, db.ForeignKey('chamas.id'), nullable=False)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'))
    mpesa_transaction_id = db.Column(db.Integer, db.ForeignKey('mpesa_transactions.id'))
    receipt_number = db.Column(db.String(100), unique=True, nullable=False)
    receipt_type = db.Column(db.String(50), nullable=False)  # contribution, loan_repayment, penalty, etc.
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    payment_method = db.Column(db.String(20), default='mpesa')
    payment_reference = db.Column(db.String(100))  # M-Pesa receipt number
    receipt_data = db.Column(db.JSON)  # Additional receipt data
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='receipts')
    chama = db.relationship('Chama', backref='receipts')
    transaction = db.relationship('Transaction', backref='receipts')
    mpesa_transaction = db.relationship('MpesaTransaction', backref='receipts')
    
    def __repr__(self):
        return f'<Receipt {self.receipt_number}'

class RecurringPayment(db.Model):
    __tablename__ = 'recurring_payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chama_id = db.Column(db.Integer, db.ForeignKey('chamas.id'), nullable=False)
    payment_type = db.Column(db.String(50), nullable=False)  # contribution, savings
    amount = db.Column(db.Float, nullable=False)
    frequency = db.Column(db.String(20), nullable=False)  # monthly, weekly, daily
    next_payment_date = db.Column(db.DateTime, nullable=False)
    auto_debit = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    phone_number = db.Column(db.String(20))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='recurring_payments')
    chama = db.relationship('Chama', backref='recurring_payments')
    
    def __repr__(self):
        return f'<RecurringPayment {self.payment_type} - {self.user.username}>'

class MultiSignatureTransaction(db.Model):
    """Model for transactions requiring multiple signatures (treasurer double-sign)"""
    __tablename__ = 'multi_signature_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    chama_id = db.Column(db.Integer, db.ForeignKey('chamas.id'), nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)  # loan_disbursement, large_expense, emergency_withdrawal
    transaction_reference_id = db.Column(db.Integer)  # Reference to loan_id, expense_id, etc.
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Requester information
    requested_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # First signature (usually treasurer)
    first_signatory_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    first_signature_at = db.Column(db.DateTime)
    first_signature_comment = db.Column(db.Text)
    
    # Second signature (usually chair/vice-chair)
    second_signatory_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    second_signature_at = db.Column(db.DateTime)
    second_signature_comment = db.Column(db.Text)
    
    # Transaction status
    status = db.Column(db.String(20), default='pending')  # pending, partially_signed, approved, rejected, executed
    rejection_reason = db.Column(db.Text)
    executed_at = db.Column(db.DateTime)
    
    # Security features
    ip_address_request = db.Column(db.String(45))
    ip_address_first_sign = db.Column(db.String(45))
    ip_address_second_sign = db.Column(db.String(45))
    
    # Additional metadata
    expires_at = db.Column(db.DateTime)  # Transaction expires if not signed within timeframe
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chama = db.relationship('Chama', backref='multi_signature_transactions')
    requested_by = db.relationship('User', foreign_keys=[requested_by_id], backref='requested_multi_sig_transactions')
    first_signatory = db.relationship('User', foreign_keys=[first_signatory_id], backref='first_signed_transactions')
    second_signatory = db.relationship('User', foreign_keys=[second_signatory_id], backref='second_signed_transactions')
    
    @property
    def is_expired(self):
        """Check if transaction has expired"""
        return self.expires_at and datetime.utcnow() > self.expires_at
    
    @property
    def signatures_required(self):
        """Get number of signatures still required"""
        if self.second_signature_at:
            return 0
        elif self.first_signature_at:
            return 1
        else:
            return 2
    
    @property
    def can_be_executed(self):
        """Check if transaction can be executed"""
        return (self.status == 'approved' and 
                self.first_signature_at and 
                self.second_signature_at and 
                not self.is_expired)
    
    def add_signature(self, signatory_id, comment=None, ip_address=None):
        """Add a signature to the transaction"""
        if self.is_expired:
            return False, "Transaction has expired"
        
        if self.status == 'rejected':
            return False, "Transaction has been rejected"
        
        if not self.first_signature_at:
            # First signature
            self.first_signatory_id = signatory_id
            self.first_signature_at = datetime.utcnow()
            self.first_signature_comment = comment
            self.ip_address_first_sign = ip_address
            self.status = 'partially_signed'
            return True, "First signature added successfully"
        
        elif not self.second_signature_at and signatory_id != self.first_signatory_id:
            # Second signature (different person)
            self.second_signatory_id = signatory_id
            self.second_signature_at = datetime.utcnow()
            self.second_signature_comment = comment
            self.ip_address_second_sign = ip_address
            self.status = 'approved'
            return True, "Second signature added successfully - Transaction approved"
        
        else:
            return False, "Invalid signature attempt"
    
    def reject_transaction(self, rejector_id, reason, ip_address=None):
        """Reject the transaction"""
        if self.is_expired:
            return False, "Transaction has expired"
        
        self.status = 'rejected'
        self.rejection_reason = reason
        self.updated_at = datetime.utcnow()
        
        # Log who rejected it
        if not self.first_signature_at:
            self.first_signatory_id = rejector_id
            self.ip_address_first_sign = ip_address
        else:
            self.second_signatory_id = rejector_id
            self.ip_address_second_sign = ip_address
        
        return True, "Transaction rejected successfully"
    
    @staticmethod
    def create_loan_disbursement_transaction(chama_id, loan_id, amount, requested_by_id, ip_address=None):
        """Create a multi-signature transaction for loan disbursement"""
        # Set expiration to 48 hours from now
        expires_at = datetime.utcnow() + timedelta(hours=48)
        
        transaction = MultiSignatureTransaction(
            chama_id=chama_id,
            transaction_type='loan_disbursement',
            transaction_reference_id=loan_id,
            amount=amount,
            description=f'Loan disbursement of KES {amount:,.2f}',
            requested_by_id=requested_by_id,
            expires_at=expires_at,
            ip_address_request=ip_address
        )
        
        return transaction
    
    @staticmethod
    def create_large_expense_transaction(chama_id, amount, description, requested_by_id, ip_address=None):
        """Create a multi-signature transaction for large expenses"""
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        transaction = MultiSignatureTransaction(
            chama_id=chama_id,
            transaction_type='large_expense',
            amount=amount,
            description=description,
            requested_by_id=requested_by_id,
            expires_at=expires_at,
            ip_address_request=ip_address
        )
        
        return transaction
    
    def __repr__(self):
        return f'<MultiSignatureTransaction {self.transaction_type} - {self.amount} - {self.status}>'
