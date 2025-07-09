"""
Daily task to send meeting reminders
This should be run as a scheduled task (cron job or similar)
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Chama, Event, chama_members
from app.routes.notifications import create_meeting_reminder
from datetime import datetime, date, timedelta

def send_meeting_reminders():
    """Send meeting reminders for meetings happening tomorrow"""
    app = create_app()
    
    with app.app_context():
        tomorrow = date.today() + timedelta(days=1)
        
        # Get all events scheduled for tomorrow
        upcoming_events = Event.query.filter(
            Event.event_date == tomorrow,
            Event.status == 'scheduled'
        ).all()
        
        # Send reminders for each event
        for event in upcoming_events:
            create_meeting_reminder(event.chama_id, event.event_date)
            print(f"Sent reminder for {event.title} in {event.chama.name}")
        
        # Also check for weekly meetings based on meeting_day
        weekday_mapping = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        tomorrow_weekday = tomorrow.weekday()
        
        # Find chamas that have meetings on tomorrow's weekday
        chamas_with_meetings = Chama.query.filter(
            Chama.meeting_day.isnot(None),
            Chama.status == 'active'
        ).all()
        
        for chama in chamas_with_meetings:
            if chama.meeting_day and weekday_mapping.get(chama.meeting_day.lower()) == tomorrow_weekday:
                # Check if there's no specific event for this date
                existing_event = Event.query.filter(
                    Event.chama_id == chama.id,
                    Event.event_date == tomorrow
                ).first()
                
                if not existing_event:
                    create_meeting_reminder(chama.id, tomorrow)
                    print(f"Sent weekly meeting reminder for {chama.name}")

if __name__ == '__main__':
    send_meeting_reminders()
