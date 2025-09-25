from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.notification_model import Notification, NotificationSettings
from app.services.notification_service import NotificationService
from app.extensions import db
from app.models.user_model import User
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/notifications/broadcast', methods=['POST'])
@jwt_required()
def broadcast_notification():
    """Broadcast notification to multiple users (admin only)"""
    try:
        # TODO: Add proper admin role check
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        # Check if user has admin role
        if current_user.role != 'admin':
            return jsonify({
                "status": 403,
                "message": "Admin access required"
            }), 403

        data = request.get_json()
        if not data:
            return jsonify({
                "status": 400,
                "message": "Request data is required"
            }), 400

        title = data.get('title')
        message = data.get('message')
        category = data.get('category', 'system')
        priority = data.get('priority', 'medium')
        notification_types = data.get('notification_types', ['in_app', 'email'])
        target_users = data.get('target_users', 'all')
        user_filters = data.get('user_filters')
        metadata = data.get('metadata')

        if not title or not message:
            return jsonify({
                "status": 400,
                "message": "Title and message are required"
            }), 400

        # Broadcast notification using service
        result = NotificationService.broadcast_notification(
            notification_data={
                'title': title,
                'message': message,
                'category': category,
                'priority': priority,
                'metadata': metadata
            },
            notification_types=notification_types,
            target_users=target_users,
            user_filters=user_filters
        )

        return jsonify({
            "status": 201,
            "message": f"Notification broadcast initiated",
            "data": result
        })

    except Exception as e:
        logger.error(f"Error broadcasting notification: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "Failed to broadcast notification",
            "error": str(e)
        }), 500

@admin_bp.route('/notifications/bulk-create', methods=['POST'])
@jwt_required()
def bulk_create_notifications():
    """Create notifications in bulk for specific users (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if current_user.role != 'admin':
            return jsonify({
                "status": 403,
                "message": "Admin access required"
            }), 403

        data = request.get_json()
        if not data:
            return jsonify({
                "status": 400,
                "message": "Request data is required"
            }), 400

        user_ids = data.get('user_ids', [])
        notifications_data = data.get('notifications', [])

        if not user_ids or not notifications_data:
            return jsonify({
                "status": 400,
                "message": "User IDs and notifications data are required"
            }), 400

        # Verify all users exist
        users = User.query.filter(User.id.in_(user_ids)).all()
        if len(users) != len(user_ids):
            return jsonify({
                "status": 400,
                "message": "Some users not found"
            }), 400

        created_count = 0
        for user in users:
            created_notifications = NotificationService.create_notifications_for_user(
                user, notifications_data
            )
            created_count += len(created_notifications)

        return jsonify({
            "status": 201,
            "message": "Bulk notifications created successfully",
            "data": {
                "users_targeted": len(users),
                "notifications_created": created_count
            }
        })

    except Exception as e:
        logger.error(f"Error bulk creating notifications: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "Failed to create bulk notifications",
            "error": str(e)
        }), 500

@admin_bp.route('/notifications/cleanup', methods=['DELETE'])
@jwt_required()
def cleanup_old_notifications():
    """Clean up old notifications (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if current_user.role != 'admin':
            return jsonify({
                "status": 403,
                "message": "Admin access required"
            }), 403

        days_to_keep = request.args.get('days', 90, type=int)
        deleted_count = NotificationService.cleanup_old_notifications(days_to_keep)

        return jsonify({
            "status": 200,
            "message": "Notifications cleaned up successfully",
            "data": {
                "deleted_count": deleted_count,
                "days_kept": days_to_keep
            }
        })

    except Exception as e:
        logger.error(f"Error cleaning up notifications: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "Failed to cleanup notifications",
            "error": str(e)
        }), 500

@admin_bp.route('/notifications/stats', methods=['GET'])
@jwt_required()
def get_global_notification_stats():
    """Get global notification statistics (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if current_user.role != 'admin':
            return jsonify({
                "status": 403,
                "message": "Admin access required"
            }), 403

        days = request.args.get('days', 30, type=int)

        # Total notifications
        total_notifications = Notification.query.count()

        # Notifications by category
        category_stats = db.session.query(
            Notification.category,
            db.func.count(Notification.id)
        ).group_by(Notification.category).all()

        # Read vs unread
        read_count = Notification.query.filter_by(is_read=True).count()
        unread_count = Notification.query.filter_by(is_read=False).count()

        # Recent notifications
        recent_count = Notification.query.filter(
            Notification.created_at >= db.func.date('now', f'-{days} days')
        ).count()

        return jsonify({
            "status": 200,
            "message": "Global notification statistics retrieved",
            "data": {
                "total_notifications": total_notifications,
                "read_notifications": read_count,
                "unread_notifications": unread_count,
                "recent_notifications": recent_count,
                "period_days": days,
                "category_breakdown": {cat: count for cat, count in category_stats}
            }
        })

    except Exception as e:
        logger.error(f"Error getting global notification stats: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "Failed to retrieve notification statistics",
            "error": str(e)
        }), 500
