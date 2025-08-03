from app import db
from datetime import datetime

class MarketplaceProduct(db.Model):
    __tablename__ = 'marketplace_products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(12,2))
    vendor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # TODO: Add more fields as needed

    def as_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': str(self.price),
            'vendor_id': self.vendor_id,
            'approved': self.approved,
            'created_at': self.created_at.isoformat()
        }
