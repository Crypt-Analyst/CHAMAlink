from app import create_app, db
from app.models import User, Chama, Transaction, Event
from datetime import datetime, date, time
import random

def seed_sample_data():
    """Seed the database with sample data for testing"""
    
    app = create_app()
    
    with app.app_context():
        # Check if sample data already exists
        if Chama.query.first():
            print("Sample data already exists!")
            return
            
        # Get the first user (should be the one we registered)
        user = User.query.first()
        if not user:
            # Create a sample user if none exists
            user = User(username='testuser', email='test@example.com')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
            print("Created sample user")
        
        # Create sample chamas
        chama1 = Chama(
            name='Smart Investors',
            description='Investment-focused chama for smart financial growth',
            goal='Build wealth through smart investments and consistent savings',
            monthly_contribution=5000.0,
            total_balance=85000.0,
            meeting_day='friday',
            meeting_time=time(14, 0),  # 2:00 PM
            status='active',
            creator_id=user.id
        )
        
        chama2 = Chama(
            name='Property Builders',
            description='Real estate investment chama',
            goal='Acquire and develop real estate properties',
            monthly_contribution=7500.0,
            total_balance=40000.0,
            meeting_day='saturday',
            meeting_time=time(10, 0),  # 10:00 AM
            status='active',
            creator_id=user.id
        )
        
        chama3 = Chama(
            name='Emergency Fund',
            description='Emergency savings and loan chama',
            goal='Build a collective emergency fund for members',
            monthly_contribution=2000.0,
            total_balance=15000.0,
            meeting_day='sunday',
            meeting_time=time(16, 0),  # 4:00 PM
            status='active',
            creator_id=user.id
        )
        
        # Add chamas to session
        db.session.add(chama1)
        db.session.add(chama2)
        db.session.add(chama3)
        db.session.commit()
        
        # Add user as member of all chamas
        chama1.members.append(user)
        chama2.members.append(user)
        chama3.members.append(user)
        
        # Create sample transactions
        transactions = [
            Transaction(
                type='contribution',
                amount=5000.0,
                description='Smart Investors - December 2024',
                user_id=user.id,
                chama_id=chama1.id,
                created_at=datetime.now().replace(hour=10, minute=0)
            ),
            Transaction(
                type='investment',
                amount=15000.0,
                description='Property Builders - Land Investment',
                user_id=user.id,
                chama_id=chama2.id,
                created_at=datetime.now().replace(day=datetime.now().day-1, hour=14, minute=30)
            ),
            Transaction(
                type='loan',
                amount=10000.0,
                description='Emergency Fund - John Doe',
                user_id=user.id,
                chama_id=chama3.id,
                created_at=datetime.now().replace(day=datetime.now().day-3, hour=9, minute=15)
            ),
            Transaction(
                type='contribution',
                amount=7500.0,
                description='Property Builders - December 2024',
                user_id=user.id,
                chama_id=chama2.id,
                created_at=datetime.now().replace(day=datetime.now().day-5, hour=11, minute=45)
            ),
            Transaction(
                type='withdrawal',
                amount=3000.0,
                description='Smart Investors - Admin fees',
                user_id=user.id,
                chama_id=chama1.id,
                created_at=datetime.now().replace(day=datetime.now().day-7, hour=16, minute=20)
            )
        ]
        
        for transaction in transactions:
            db.session.add(transaction)
        
        # Create sample events
        events = [
            Event(
                title='Smart Investors Meeting',
                description='Monthly review and planning session',
                event_date=date(2025, 1, 15),
                event_time=time(14, 0),
                location='Conference Room A',
                type='meeting',
                chama_id=chama1.id,
                creator_id=user.id
            ),
            Event(
                title='Contribution Deadline',
                description='Monthly contribution deadline for Property Builders',
                event_date=date(2025, 1, 20),
                type='deadline',
                chama_id=chama2.id,
                creator_id=user.id
            ),
            Event(
                title='Investment Opportunity Review',
                description='Review new investment opportunities',
                event_date=date(2025, 1, 25),
                event_time=time(10, 0),
                location='Online Meeting',
                type='meeting',
                chama_id=chama1.id,
                creator_id=user.id
            ),
            Event(
                title='Property Site Visit',
                description='Visit potential property acquisition site',
                event_date=date(2025, 1, 30),
                event_time=time(9, 0),
                location='Nairobi CBD',
                type='event',
                chama_id=chama2.id,
                creator_id=user.id
            )
        ]
        
        for event in events:
            db.session.add(event)
        
        db.session.commit()
        print("Sample data seeded successfully!")
        print(f"Created {len([chama1, chama2, chama3])} chamas")
        print(f"Created {len(transactions)} transactions")
        print(f"Created {len(events)} events")

if __name__ == '__main__':
    seed_sample_data()
