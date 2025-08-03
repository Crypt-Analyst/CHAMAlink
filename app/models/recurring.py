from app import db
from datetime import datetime

class RecurringPayment(db.Model):
    __tablename__ = 'recurring_payments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Numeric(12,2), nullable=False)
    frequency = db.Column(db.String(32))  # e.g., 'monthly', 'weekly'
    next_due = db.Column(db.DateTime)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # TODO: Add more fields as needed
