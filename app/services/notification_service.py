from app.models.notification_model import Notification, NotificationSettings
from app.extensions import db
from app.services.email_service import EmailService
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    """Service class for handling notification operations"""

    @staticmethod
    def create_notification(user_id, title, message, category='system', priority='medium', metadata=None):
        """Create a single notification"""
        try:
            notification = Notification.create_notification(
                user_id=user_id,
                title=title,
                message=message,
                category=category,
                priority=priority,
                metadata=metadata
            )
            db.session.add(notification)
            db.session.commit()
            return notification
        except Exception as e:
            logger.error(f"Failed to create notification: {str(e)}")
            db.session.rollback()
            return None

    @staticmethod
    def create_notifications_for_user(user, notifications_data):
        """Create multiple notifications for a user"""
        created_notifications = []

        for notif_data in notifications_data:
            notification = NotificationService.create_notification(
                user_id=user.id,
                title=notif_data.get('title', 'Notification'),
                message=notif_data.get('message', ''),
                category=notif_data.get('category', 'system'),
                priority=notif_data.get('priority', 'medium'),
                metadata=notif_data.get('metadata')
            )

            if notification:
                created_notifications.append(notification)

                # Send email if enabled
                settings = NotificationSettings.query.filter_by(user_id=user.id).first()
                if not settings:
                    settings = NotificationSettings.create_default_settings(user.id)
                    db.session.add(settings)

                if settings.should_send_email(notification.category):
                    NotificationService._send_notification_email(user, notification)

        db.session.commit()
        return created_notifications

    @staticmethod
    def broadcast_notification(notification_data, notification_types=None, target_users='all', user_filters=None):
        """
        Broadcast notification to multiple users

        Args:
            notification_data: Dict with title, message, category, priority, metadata
            notification_types: List of ['in_app', 'email'] (default: both)
            target_users: 'all', 'verified', 'active', or list of user IDs
            user_filters: Additional filter criteria
        """
        if notification_types is None:
            notification_types = ['in_app', 'email']

        # Get target users
        users = NotificationService._get_target_users(target_users, user_filters)

        title = notification_data.get('title', 'System Notification')
        message = notification_data.get('message', '')
        category = notification_data.get('category', 'system')
        priority = notification_data.get('priority', 'medium')
        metadata = notification_data.get('metadata')

        created_notifications = []
        emails_sent = 0

        for user in users:
            try:
                # Check or create user notification settings
                settings = NotificationSettings.query.filter_by(user_id=user.id).first()
                if not settings:
                    settings = NotificationSettings.create_default_settings(user.id)
                    db.session.add(settings)

                # Create in-app notification for all users by default
                if 'in_app' in notification_types:
                    notification = Notification.create_notification(
                        user_id=user.id,
                        title=title,
                        message=message,
                        category=category,
                        priority=priority,
                        metadata=metadata
                    )
                    db.session.add(notification)
                    created_notifications.append(notification)

                # Send email notification if enabled in user settings
                if 'email' in notification_types and settings.should_send_email(category):
                    success = NotificationService._send_notification_email(user, notification)
                    if success:
                        emails_sent += 1

            except Exception as e:
                logger.error(f"Failed to create notification for user {user.id}: {str(e)}")
                continue

        db.session.commit()

        return {
            'total_users': len(users),
            'notifications_created': len(created_notifications),
            'emails_sent': emails_sent,
            'success': True
        }

    @staticmethod
    def _get_target_users(target_users='all', user_filters=None):
        """Get target users based on criteria"""
        from app.models.user_model import User

        query = User.query

        if target_users == 'verified':
            query = query.filter(User.email_verified == True)
        elif target_users == 'active':
            # Consider users active if they have logged in within 30 days
            from datetime import datetime, timedelta
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            query = query.filter(User.updated_at >= thirty_days_ago)
        elif isinstance(target_users, list):
            query = query.filter(User.id.in_(target_users))
        # 'all' doesn't need additional filtering

        # Apply additional filters if provided
        if user_filters:
            for key, value in user_filters.items():
                if hasattr(User, key):
                    query = query.filter(getattr(User, key) == value)

        return query.all()

    @staticmethod
    def _send_notification_email(user, notification):
        """Send email notification for a specific notification"""
        try:
            if notification.category == 'security':
                return EmailService.send_security_alert_email(
                    user.email,
                    user.name,
                    notification.title,
                    notification.message
                )
            elif notification.category == 'transaction':
                return EmailService.send_transaction_email(
                    user.email,
                    user.name,
                    notification.title,
                    notification.message
                )
            elif notification.category == 'system':
                return EmailService.send_system_notification_email(
                    user.email,
                    user.name,
                    notification.title,
                    notification.message,
                    notification.category
                )
            else:
                return EmailService.send_system_notification_email(
                    user.email,
                    user.name,
                    notification.title,
                    notification.message,
                    notification.category
                )
        except Exception as e:
            logger.error(f"Failed to send notification email to {user.email}: {str(e)}")
            return False

    @staticmethod
    def send_welcome_notification(user):
        """Send welcome notification to new user"""
        try:
            # Create in-app notification
            welcome_notification = Notification(
                user_id=user.id,
                title="Welcome to Swipe Payment!",
                message="Your account has been created successfully. You can now send and receive payments.",
                category="system",
                priority="medium"
            )
            db.session.add(welcome_notification)

            # Send welcome email
            EmailService.send_welcome_email(user.email, user.name)

            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to send welcome notification: {str(e)}")
            db.session.rollback()
            return False

    @staticmethod
    def get_user_notification_stats(user_id, days=30):
        """Get notification statistics for a user"""
        from datetime import datetime, timedelta
        from sqlalchemy import func

        start_date = datetime.utcnow() - timedelta(days=days)

        # Basic statistics
        total_notifications = Notification.query.filter(
            Notification.user_id == user_id,
            Notification.created_at >= start_date
        ).count()

        read_notifications = Notification.query.filter(
            Notification.user_id == user_id,
            Notification.is_read == True,
            Notification.created_at >= start_date
        ).count()

        # Category breakdown
        category_stats = db.session.query(
            Notification.category,
            func.count(Notification.id)
        ).filter(
            Notification.user_id == user_id,
            Notification.created_at >= start_date
        ).group_by(Notification.category).all()

        # Response time analysis
        avg_response_time = db.session.query(
            func.avg(
                func.strftime('%s', Notification.read_at) -
                func.strftime('%s', Notification.created_at)
            )
        ).filter(
            Notification.user_id == user_id,
            Notification.is_read == True,
            Notification.created_at >= start_date
        ).scalar()

        return {
            'total_notifications': total_notifications,
            'read_notifications': read_notifications,
            'unread_notifications': total_notifications - read_notifications,
            'read_rate': read_notifications / total_notifications if total_notifications > 0 else 0,
            'category_breakdown': {cat: count for cat, count in category_stats},
            'avg_response_time_minutes': avg_response_time / 60 if avg_response_time else None,
            'period_days': days
        }

    @staticmethod
    def cleanup_old_notifications(days_to_keep=90):
        """Clean up old notifications"""
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        deleted_count = Notification.query.filter(
            Notification.created_at < cutoff_date
        ).delete()

        db.session.commit()
        logger.info(f"Cleaned up {deleted_count} old notifications")
        return deleted_count
