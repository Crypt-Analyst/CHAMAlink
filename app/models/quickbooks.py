from app import db
from datetime import datetime

class QuickBooksIntegration(db.Model):
    """Model for storing QuickBooks integration details"""
    __tablename__ = 'quickbooks_integrations'
    
    id = db.Column(db.Integer, primary_key=True)
    chama_id = db.Column(db.Integer, db.ForeignKey('chamas.id'), nullable=True)  # nullable for global connections
    company_id = db.Column(db.String(255), nullable=False)  # QuickBooks Company ID (Realm ID)
    access_token = db.Column(db.Text, nullable=True)
    refresh_token = db.Column(db.Text, nullable=True)
    token_expires_at = db.Column(db.DateTime, nullable=True)
    connected_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_sync = db.Column(db.DateTime, nullable=True)
    sync_status = db.Column(db.String(50), default='active')  # active, inactive, error
    sync_settings = db.Column(db.JSON, default={})  # Store sync preferences
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    chama = db.relationship('Chama', backref='quickbooks_integration', lazy=True)
    
    def __repr__(self):
        return f'<QuickBooksIntegration chama_id={self.chama_id} company_id={self.company_id}>'
    
    @property
    def is_token_valid(self):
        """Check if access token is still valid"""
        if not self.token_expires_at:
            return False
        return datetime.utcnow() < self.token_expires_at
    
    @property
    def days_since_last_sync(self):
        """Get days since last sync"""
        if not self.last_sync:
            return None
        return (datetime.utcnow() - self.last_sync).days
    
    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            'id': self.id,
            'chama_id': self.chama_id,
            'company_id': self.company_id,
            'connected_at': self.connected_at.isoformat() if self.connected_at else None,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'sync_status': self.sync_status,
            'is_token_valid': self.is_token_valid,
            'days_since_last_sync': self.days_since_last_sync
        }

class QuickBooksSyncLog(db.Model):
    """Model for logging QuickBooks sync operations"""
    __tablename__ = 'quickbooks_sync_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    integration_id = db.Column(db.Integer, db.ForeignKey('quickbooks_integrations.id'), nullable=False)
    sync_type = db.Column(db.String(50), nullable=False)  # full, incremental, manual
    status = db.Column(db.String(20), nullable=False)  # success, error, partial
    records_processed = db.Column(db.Integer, default=0)
    records_synced = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text, nullable=True)
    sync_data = db.Column(db.JSON, default={})  # Store detailed sync information
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationship
    integration = db.relationship('QuickBooksIntegration', backref='sync_logs', lazy=True)
    
    def __repr__(self):
        return f'<QuickBooksSyncLog id={self.id} status={self.status}>'
    
    @property
    def duration_seconds(self):
        """Get sync duration in seconds"""
        if not self.completed_at:
            return None
        return (self.completed_at - self.started_at).total_seconds()
    
    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            'id': self.id,
            'sync_type': self.sync_type,
            'status': self.status,
            'records_processed': self.records_processed,
            'records_synced': self.records_synced,
            'error_message': self.error_message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds
        }
