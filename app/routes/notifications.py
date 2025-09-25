from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.notification_model import Notification, NotificationSettings
from app.services.notification_service import NotificationService
from app.extensions import db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@notifications_bp.route('/count', methods=['GET'])
@jwt_required()
def get_notification_count():
    """Get notification count for authenticated user"""
    try:
        user_id = get_jwt_identity()
        total_count = Notification.query.filter_by(user_id=user_id).count()
        unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()

        # Category breakdown
        category_stats = db.session.query(
            Notification.category,
            db.func.count(Notification.id)
        ).filter_by(user_id=user_id).group_by(Notification.category).all()

        category_breakdown = {category: count for category, count in category_stats}

        return jsonify({
            "status": 200,
            "message": "Notification count retrieved successfully",
            "data": {
                "total": total_count,
                "unread": unread_count,
                "categories": category_breakdown
            }
        })
    except Exception as e:
        logger.error(f"Error getting notification count: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "Failed to retrieve notification count",
            "error": str(e)
        }), 500

@notifications_bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get paginated notifications for authenticated user"""
    try:
        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        limit = min(request.args.get('limit', 20, type=int), 100)
        category = request.args.get('category')
        status = request.args.get('status')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')

        # Build query with filters
        query = Notification.query.filter_by(user_id=user_id)

        if category:
            query = query.filter_by(category=category)

        if status == 'read':
            query = query.filter_by(is_read=True)
        elif status == 'unread':
            query = query.filter_by(is_read=False)

        # Apply sorting
        if sort_order == 'asc':
            query = query.order_by(getattr(Notification, sort_by).asc())
        else:
            query = query.order_by(getattr(Notification, sort_by).desc())

        # Pagination
        pagination = query.paginate(page=page, per_page=limit, error_out=False)
        notifications = pagination.items

        return jsonify({
            "status": 200,
            "message": "Notifications retrieved successfully",
            "data": {
                "notifications": [notif.to_dict() for notif in notifications],
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": pagination.total,
                    "pages": pagination.pages,
                    "has_next": pagination.has_next,
                    "has_prev": pagination.has_prev
                }
            }
        })
    except Exception as e:
        logger.error(f"Error getting notifications: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "Failed to retrieve notifications",
            "error": str(e)
        }), 500

@notifications_bp.route('/<notification_id>', methods=['GET'])
@jwt_required()
def get_notification(notification_id):
    """Get specific notification by ID"""
    try:
        user_id = get_jwt_identity()

        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()

        if not notification:
            return jsonify({
                "status": 404,
                "message": "Notification not found"
            }), 404

        return jsonify({
            "status": 200,
            "message": "Notification retrieved successfully",
            "data": notification.to_dict()
        })
    except Exception as e:
        logger.error(f"Error getting notification: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "Failed to retrieve notification",
            "error": str(e)
        }), 500

@notifications_bp.route('/<notification_id>/read', methods=['PATCH'])
@jwt_required()
def toggle_notification_read(notification_id):
    """Mark notification as read/unread"""
    try:
        user_id = get_jwt_identity()

        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()

        if not notification:
            return jsonify({
                "status": 404,
                "message": "Notification not found"
            }), 404

        data = request.get_json()
        is_read = data.get('is_read', True)

        if is_read:
            notification.mark_as_read()
        else:
            notification.mark_as_unread()

        db.session.commit()

        return jsonify({
            "status": 200,
            "message": "Notification updated successfully",
            "data": {
                "id": notification.id,
                "is_read": notification.is_read,
                "read_at": notification.read_at.isoformat() if notification.read_at else None
            }
        })
    except Exception as e:
        logger.error(f"Error updating notification: {str(e)}")
        db.session.rollback()
        return jsonify({
            "status": 500,
            "message": "Failed to update notification",
            "error": str(e)
        }), 500

@notifications_bp.route('/bulk/read', methods=['PATCH'])
@jwt_required()
def bulk_toggle_notifications():
    """Bulk mark notifications as read/unread"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        notification_ids = data.get('notification_ids', [])
        is_read = data.get('is_read', True)

        if not notification_ids:
            return jsonify({
                "status": 400,
                "message": "No notification IDs provided"
            }), 400

        # Verify all notifications belong to user
        notifications = Notification.query.filter(
            Notification.id.in_(notification_ids),
            Notification.user_id == user_id
        ).all()

        if len(notifications) != len(notification_ids):
            return jsonify({
                "status": 400,
                "message": "Some notifications not found or don't belong to user"
            }), 400

        # Update notifications
        updated_ids = []
        for notification in notifications:
            if is_read:
                notification.mark_as_read()
            else:
                notification.mark_as_unread()
            updated_ids.append(str(notification.id))

        db.session.commit()

        return jsonify({
            "status": 200,
            "message": f"Notifications updated successfully",
            "data": {
                "updated_count": len(updated_ids),
                "updated_ids": updated_ids
            }
        })
    except Exception as e:
        logger.error(f"Error bulk updating notifications: {str(e)}")
        db.session.rollback()
        return jsonify({
            "status": 500,
            "message": "Failed to update notifications",
            "error": str(e)
        }), 500

@notifications_bp.route('/clear', methods=['DELETE'])
@jwt_required()
def clear_notifications():
    """Clear notifications with optional filtering"""
    try:
        user_id = get_jwt_identity()
        category = request.args.get('category')
        older_than = request.args.get('older_than')
        status = request.args.get('status')

        query = Notification.query.filter_by(user_id=user_id)

        if category:
            query = query.filter_by(category=category)

        if older_than:
            try:
                older_than_date = datetime.fromisoformat(older_than.replace('Z', '+00:00'))
                query = query.filter(Notification.created_at < older_than_date)
            except ValueError:
                return jsonify({
                    "status": 400,
                    "message": "Invalid date format for older_than parameter"
                }), 400

        if status == 'read':
            query = query.filter_by(is_read=True)
        elif status == 'unread':
            query = query.filter_by(is_read=False)

        deleted_count = query.count()
        query.delete()
        db.session.commit()

        return jsonify({
            "status": 200,
            "message": "Notifications cleared successfully",
            "data": {
                "deleted_count": deleted_count
            }
        })
    except Exception as e:
        logger.error(f"Error clearing notifications: {str(e)}")
        db.session.rollback()
        return jsonify({
            "status": 500,
            "message": "Failed to clear notifications",
            "error": str(e)
        }), 500

@notifications_bp.route('/settings', methods=['GET', 'PUT'])
@jwt_required()
def manage_notification_settings():
    """Get or update notification settings"""
    try:
        user_id = get_jwt_identity()

        if request.method == 'GET':
            # Get current settings
            settings = NotificationSettings.query.filter_by(user_id=user_id).first()
            if not settings:
                settings = NotificationSettings.create_default_settings(user_id)
                db.session.add(settings)
                db.session.commit()

            return jsonify({
                "status": 200,
                "message": "Notification settings retrieved",
                "data": settings.to_dict()
            })

        elif request.method == 'PUT':
            # Update settings
            settings = NotificationSettings.query.filter_by(user_id=user_id).first()
            if not settings:
                settings = NotificationSettings.create_default_settings(user_id)
                db.session.add(settings)

            data = request.get_json()

            # Update email preferences
            for category in ['security', 'transaction', 'system', 'marketing']:
                email_field = f'email_{category}'
                in_app_field = f'in_app_{category}'
                if email_field in data:
                    setattr(settings, email_field, data[email_field])
                if in_app_field in data:
                    setattr(settings, in_app_field, data[in_app_field])

            # Update push preferences
            if 'push_enabled' in data:
                settings.push_enabled = data['push_enabled']

            # Update quiet hours if provided
            if 'quiet_hours_start' in data and data['quiet_hours_start']:
                settings.quiet_hours_start = datetime.strptime(data['quiet_hours_start'], '%H:%M').time()
            if 'quiet_hours_end' in data and data['quiet_hours_end']:
                settings.quiet_hours_end = datetime.strptime(data['quiet_hours_end'], '%H:%M').time()
            if 'quiet_hours_enabled' in data:
                settings.quiet_hours_enabled = data['quiet_hours_enabled']

            db.session.commit()

            return jsonify({
                "status": 200,
                "message": "Notification settings updated",
                "data": settings.to_dict()
            })
    except Exception as e:
        logger.error(f"Error managing notification settings: {str(e)}")
        db.session.rollback()
        return jsonify({
            "status": 500,
            "message": "Failed to manage notification settings",
            "error": str(e)
        }), 500

@notifications_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_notification_stats():
    """Get notification statistics for user"""
    try:
        user_id = get_jwt_identity()
        days = request.args.get('days', 30, type=int)

        stats = NotificationService.get_user_notification_stats(user_id, days)

        return jsonify({
            "status": 200,
            "message": "Notification statistics retrieved",
            "data": stats
        })
    except Exception as e:
        logger.error(f"Error getting notification stats: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "Failed to retrieve notification statistics",
            "error": str(e)
        }), 500
