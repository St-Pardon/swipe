from app.extensions import db
from app.utils.guid_utils import GUID
from datetime import datetime
import uuid
import json
from enum import Enum

class NotificationCategory(Enum):
    SECURITY = "security"
    TRANSACTION = "transaction"
    SYSTEM = "system"
    ACCOUNT = "account"
    MARKETING = "marketing"

class NotificationPriority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Notification(db.Model):
    __tablename__ = 'notification'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(GUID(), db.ForeignKey('user.id'), nullable=False)

    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False, default=NotificationCategory.SYSTEM.value)
    priority = db.Column(db.String(20), nullable=False, default=NotificationPriority.MEDIUM.value)

    is_read = db.Column(db.Boolean, nullable=False, default=False)
    read_at = db.Column(db.DateTime)

    # Metadata for additional context (stored as JSON string for SQLite compatibility)
    extra_data = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('notifications', lazy=True))

    __table_args__ = (
        db.Index('idx_notification_user_category', 'user_id', 'category'),
        db.Index('idx_notification_user_read', 'user_id', 'is_read'),
        db.Index('idx_notification_created', 'created_at'),
        db.Index('idx_notification_priority', 'priority'),
    )

    def to_dict(self):
        """Convert notification to dictionary for API responses"""
        # Parse extra_data as JSON if it exists
        metadata = None
        if self.extra_data:
            try:
                metadata = json.loads(self.extra_data)
            except (json.JSONDecodeError, TypeError):
                metadata = self.extra_data
        
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'title': self.title,
            'message': self.message,
            'category': self.category,
            'priority': self.priority,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'metadata': metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def create_notification(cls, user_id, title, message, category='system', priority='medium', metadata=None):
        """Create a new notification"""
        # Convert metadata to JSON string if provided
        extra_data = None
        if metadata:
            try:
                extra_data = json.dumps(metadata)
            except (TypeError, ValueError):
                extra_data = str(metadata)
        
        notification = cls(
            user_id=user_id,
            title=title,
            message=message,
            category=category,
            priority=priority,
            extra_data=extra_data
        )
        return notification

    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()

    def mark_as_unread(self):
        """Mark notification as unread"""
        self.is_read = False
        self.read_at = None

class NotificationSettings(db.Model):
    __tablename__ = 'notification_settings'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(GUID(), db.ForeignKey('user.id'), nullable=False)

    # Email preferences (ALL ENABLED BY DEFAULT)
    email_security = db.Column(db.Boolean, default=True)    # Security alerts via email
    email_transaction = db.Column(db.Boolean, default=True)  # Transaction confirmations
    email_system = db.Column(db.Boolean, default=True)      # System announcements
    email_marketing = db.Column(db.Boolean, default=False)  # Marketing (opt-in only)

    # In-app preferences (ALL ENABLED BY DEFAULT)
    in_app_security = db.Column(db.Boolean, default=True)    # Security alerts in-app
    in_app_transaction = db.Column(db.Boolean, default=True)  # Transaction confirmations
    in_app_system = db.Column(db.Boolean, default=True)      # System announcements
    in_app_marketing = db.Column(db.Boolean, default=False)  # Marketing (opt-in only)

    # Push notification preferences
    push_enabled = db.Column(db.Boolean, default=True)
    push_security = db.Column(db.Boolean, default=True)
    push_transaction = db.Column(db.Boolean, default=True)
    push_system = db.Column(db.Boolean, default=False)

    # Quiet hours
    quiet_hours_start = db.Column(db.Time, nullable=True)
    quiet_hours_end = db.Column(db.Time, nullable=True)
    quiet_hours_enabled = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('notification_settings', uselist=False))

    def to_dict(self):
        """Convert settings to dictionary for API responses"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'email_security': self.email_security,
            'email_transaction': self.email_transaction,
            'email_system': self.email_system,
            'email_marketing': self.email_marketing,
            'in_app_security': self.in_app_security,
            'in_app_transaction': self.in_app_transaction,
            'in_app_system': self.in_app_system,
            'in_app_marketing': self.in_app_marketing,
            'push_enabled': self.push_enabled,
            'push_security': self.push_security,
            'push_transaction': self.push_transaction,
            'push_system': self.push_system,
            'quiet_hours_start': self.quiet_hours_start.strftime('%H:%M') if self.quiet_hours_start else None,
            'quiet_hours_end': self.quiet_hours_end.strftime('%H:%M') if self.quiet_hours_end else None,
            'quiet_hours_enabled': self.quiet_hours_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def create_default_settings(cls, user_id):
        """Create default notification settings for new users"""
        settings = cls(
            user_id=user_id,
            # Email notifications enabled for all important categories
            email_security=True,
            email_transaction=True,
            email_system=True,
            email_marketing=False,
            # In-app notifications enabled for all categories
            in_app_security=True,
            in_app_transaction=True,
            in_app_system=True,
            in_app_marketing=False,
            # Push notifications enabled by default
            push_enabled=True,
            push_security=True,
            push_transaction=True,
            push_system=False
        )
        return settings

    def get_email_enabled(self, category):
        """Check if email notifications are enabled for a category"""
        field_name = f'email_{category}'
        return getattr(self, field_name, False)

    def get_in_app_enabled(self, category):
        """Check if in-app notifications are enabled for a category"""
        field_name = f'in_app_{category}'
        return getattr(self, field_name, False)

    def should_send_email(self, category):
        """Determine if email should be sent for a notification category"""
        return self.get_email_enabled(category)

    def should_send_in_app(self, category):
        """Determine if in-app notification should be created for a category"""
        return self.get_in_app_enabled(category)
