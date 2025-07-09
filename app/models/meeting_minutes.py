from app import db
from datetime import datetime

class MeetingMinutes(db.Model):
    __tablename__ = 'meeting_minutes'
    
    id = db.Column(db.Integer, primary_key=True)
    chama_id = db.Column(db.Integer, db.ForeignKey('chamas.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=True)
    secretary_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    meeting_date = db.Column(db.Date, nullable=False)
    meeting_title = db.Column(db.String(200), nullable=False)
    attendees = db.Column(db.JSON)
    agenda_items = db.Column(db.JSON)
    decisions_made = db.Column(db.Text)
    action_items = db.Column(db.JSON)
    minutes_content = db.Column(db.Text)
    attachment_path = db.Column(db.String(500))
    status = db.Column(db.String(20), default='draft')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    
    # Relationships
    chama = db.relationship('Chama', backref='meeting_minutes')
    secretary = db.relationship('User', foreign_keys=[secretary_id], backref='minutes_recorded')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='minutes_approved')
    event = db.relationship('Event', backref='minutes')

class ChamaAnnouncement(db.Model):
    __tablename__ = 'chama_announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    chama_id = db.Column(db.Integer, db.ForeignKey('chamas.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    announcement_type = db.Column(db.String(50), default='general')
    priority = db.Column(db.String(10), default='normal')
    target_members = db.Column(db.JSON)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    # Relationships
    chama = db.relationship('Chama', backref='announcements')
    admin = db.relationship('User', backref='announcements_sent')
