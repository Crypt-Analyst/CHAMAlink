import unittest
from app import create_app, db
from app.models.user import User
from app.models.subscription import SubscriptionPlan
from flask import url_for

class SystemFeatureTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            # Avoid duplicate plan creation
            plan = SubscriptionPlan.query.filter_by(name='Pro').first()
            if not plan:
                plan = SubscriptionPlan(name='Pro', price=100, currency='KES', interval='monthly', description='Pro plan', max_chamas=1)
                db.session.add(plan)
                db.session.commit()

    def register_and_login(self):
        # Register
        self.client.post('/auth/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Testpass123!',
            'confirm': 'Testpass123!'
        })
        # Login
        self.client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'Testpass123!'
        })

    def test_onboarding_and_language(self):
        self.register_and_login()
        self.client.get('/onboarding/welcome')
        self.client.get('/onboarding/faq')
        self.client.post('/preferences/language/en')
        self.client.post('/preferences/language/sw')

    def test_api_docs_and_marketplace(self):
        self.client.get('/api/docs')
        self.client.get('/marketplace')

    def test_subscription_and_payments(self):
        self.register_and_login()
        # Subscribe with each payment method
        for method in ['mpesa', 'stripe', 'paypal', 'bank', 'manual']:
            self.client.post('/subscribe/1', data={'payment_method': method})
        self.client.get('/billing/manage')

    def test_webhook_registration_and_trigger(self):
        self.register_and_login()
        self.client.post('/api/v1/webhooks/register', json={'url': 'https://example.com/webhook', 'event': 'test'})
        self.client.post('/api/v1/webhooks/trigger', json={'event': 'test', 'payload': {'foo': 'bar'}})

    def test_admin_dashboard(self):
        # Create super admin
        with self.app.app_context():
            admin = User(username='admin', email='admin@example.com', is_super_admin=True)
            admin.set_password('Adminpass123!')
            db.session.add(admin)
            db.session.commit()
        self.client.post('/auth/login', data={'username': 'admin', 'password': 'Adminpass123!'})
        self.client.get('/admin')
        self.client.get('/admin/webhooks')
        self.client.get('/admin/api-keys')

if __name__ == '__main__':
    unittest.main()
