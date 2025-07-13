from datetime import datetime
from app import db

class Currency(db.Model):
    __tablename__ = 'currencies'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(3), nullable=False, unique=True)  # USD, KES, UGX, etc.
    name = db.Column(db.String(50), nullable=False)
    symbol = db.Column(db.String(5), nullable=False)
    exchange_rate_to_usd = db.Column(db.Float, nullable=False, default=1.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chamas = db.relationship('Chama', backref='currency_ref', lazy=True, foreign_keys='Chama.default_currency_id')
    transactions = db.relationship('Transaction', backref='currency_ref', lazy=True, foreign_keys='Transaction.currency_id')
    
    def __repr__(self):
        return f'<Currency {self.code}: {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'symbol': self.symbol,
            'exchange_rate_to_usd': self.exchange_rate_to_usd,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_default_currencies():
        """Get list of default currencies to populate the system"""
        return [
            {'code': 'USD', 'name': 'US Dollar', 'symbol': '$', 'exchange_rate_to_usd': 1.0},
            {'code': 'KES', 'name': 'Kenyan Shilling', 'symbol': 'KSh', 'exchange_rate_to_usd': 0.0077},
            {'code': 'UGX', 'name': 'Ugandan Shilling', 'symbol': 'USh', 'exchange_rate_to_usd': 0.00027},
            {'code': 'TZS', 'name': 'Tanzanian Shilling', 'symbol': 'TSh', 'exchange_rate_to_usd': 0.00043},
            {'code': 'EUR', 'name': 'Euro', 'symbol': '€', 'exchange_rate_to_usd': 1.09},
            {'code': 'GBP', 'name': 'British Pound', 'symbol': '£', 'exchange_rate_to_usd': 1.27}
        ]
    
    @classmethod
    def seed_currencies(cls):
        """Seed the database with default currencies"""
        for currency_data in cls.get_default_currencies():
            existing = cls.query.filter_by(code=currency_data['code']).first()
            if not existing:
                currency = cls(
                    code=currency_data['code'],
                    name=currency_data['name'],
                    symbol=currency_data['symbol'],
                    exchange_rate_to_usd=currency_data['exchange_rate_to_usd']
                )
                db.session.add(currency)
        
        try:
            db.session.commit()
            print("✅ Default currencies seeded successfully")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error seeding currencies: {e}")
    
    def convert_to_usd(self, amount):
        """Convert amount in this currency to USD"""
        return amount * self.exchange_rate_to_usd
    
    def convert_from_usd(self, usd_amount):
        """Convert USD amount to this currency"""
        return usd_amount / self.exchange_rate_to_usd if self.exchange_rate_to_usd > 0 else 0
    
    def convert_to_currency(self, amount, target_currency):
        """Convert amount from this currency to target currency"""
        if isinstance(target_currency, str):
            target_currency = Currency.query.filter_by(code=target_currency).first()
        
        if not target_currency:
            return amount
        
        # Convert to USD first, then to target currency
        usd_amount = self.convert_to_usd(amount)
        return target_currency.convert_from_usd(usd_amount)
    
    def update_exchange_rate(self, new_rate):
        """Update the exchange rate for this currency"""
        self.exchange_rate_to_usd = new_rate
        self.updated_at = datetime.utcnow()
        db.session.commit()
