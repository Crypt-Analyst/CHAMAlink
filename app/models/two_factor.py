from app import db
from datetime import datetime, timedelta

class TwoFactorCode(db.Model):
    __tablename__ = 'two_factor_codes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    code = db.Column(db.String(8), nullable=False)
    method = db.Column(db.String(16), default='sms')  # sms, email, app
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=10))
    is_used = db.Column(db.Boolean, default=False)

    def is_expired(self):
        return datetime.utcnow() > self.expires_at
