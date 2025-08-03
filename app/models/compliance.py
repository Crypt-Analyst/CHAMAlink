from app import db
from datetime import datetime

class KYCRecord(db.Model):
    __tablename__ = 'kyc_records'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    document_type = db.Column(db.String(64))
    document_url = db.Column(db.String(256))
    verified = db.Column(db.Boolean, default=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime)
    # TODO: Add more fields as needed
