from app import db
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    chama_id = Column(Integer, ForeignKey('chamas.id'), nullable=True)  # Optional, for chama-specific notifications
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), nullable=False, default='info')  # info, warning, success, error, system
    is_read = Column(Boolean, nullable=True, default=False)
    created_date = Column(DateTime, nullable=True, default=datetime.utcnow)
    related_id = Column(Integer, nullable=True)  # For linking to other entities
    
    # Relationships
    user = relationship('User', backref='notifications')
    chama = relationship('Chama', backref='notifications', foreign_keys=[chama_id])
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.title} for User {self.user_id}>'
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            db.session.commit()
    
    def to_dict(self):
        """Convert notification to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'chama_id': self.chama_id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'is_read': self.is_read,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'related_id': self.related_id,
            'chama_name': self.chama.name if self.chama else None
        }
    
    @staticmethod
    def create_system_notification(user_id, title, message, priority='info'):
        """Create a system notification for a user"""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type='system'
        )
        db.session.add(notification)
        return notification
    
    @staticmethod
    def create_chama_notification(user_id, chama_id, title, message, notification_type='info'):
        """Create a chama-related notification for a user"""
        notification = Notification(
            user_id=user_id,
            chama_id=chama_id,
            title=title,
            message=message,
            type=notification_type
        )
        db.session.add(notification)
        return notification
    
    @staticmethod
    def get_unread_count(user_id):
        """Get count of unread notifications for a user"""
        return Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).count()
    
    @staticmethod
    def get_user_notifications(user_id, limit=50, unread_only=False):
        """Get notifications for a user"""
        query = Notification.query.filter_by(user_id=user_id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        return query.order_by(Notification.created_date.desc()).limit(limit).all()
