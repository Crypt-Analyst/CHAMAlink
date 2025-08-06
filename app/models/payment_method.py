from app import db

class PaymentMethod(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, unique=True)
    is_enabled = db.Column(db.Boolean, default=True)
    description = db.Column(db.String(128))

# Predefined methods: MPESA, Stripe, PayPal, Card, Bank
