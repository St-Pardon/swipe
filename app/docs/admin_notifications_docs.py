from flask_restx import Resource
from flask_jwt_extended import jwt_required
from app.swagger import admin_notifications_ns
from app.api_docs import (
    success_model,
    error_model,
    broadcast_notification_model,
    bulk_notification_request_model
)


@admin_notifications_ns.route('/notifications/broadcast')
class AdminBroadcastNotification(Resource):
    @admin_notifications_ns.doc('broadcast_notification', security='Bearer')
    @admin_notifications_ns.expect(broadcast_notification_model)
    @admin_notifications_ns.marshal_with(success_model, code=201)
    @admin_notifications_ns.response(401, 'Unauthorized', error_model)
    @admin_notifications_ns.response(403, 'Admin access required', error_model)
    @admin_notifications_ns.response(500, 'Failed to broadcast notification', error_model)
    @jwt_required()
    def post(self):
        """
        Broadcast a notification to a targeted audience. Admin role required.
        """
        pass  # Implementation handled by `app/routes/admin_notifications.py`


@admin_notifications_ns.route('/notifications/bulk-create')
class AdminBulkNotifications(Resource):
    @admin_notifications_ns.doc('bulk_create_notifications', security='Bearer')
    @admin_notifications_ns.expect(bulk_notification_request_model)
    @admin_notifications_ns.marshal_with(success_model, code=201)
    @admin_notifications_ns.response(400, 'Invalid request payload', error_model)
    @admin_notifications_ns.response(401, 'Unauthorized', error_model)
    @admin_notifications_ns.response(403, 'Admin access required', error_model)
    @admin_notifications_ns.response(500, 'Failed to create notifications', error_model)
    @jwt_required()
    def post(self):
        """
        Create notifications in bulk for specific users. Admin role required.
        """
        pass


@admin_notifications_ns.route('/notifications/cleanup')
class AdminCleanupNotifications(Resource):
    @admin_notifications_ns.doc('cleanup_notifications', security='Bearer')
    @admin_notifications_ns.param('days', 'Number of days to keep notifications (default: 90)', type='int')
    @admin_notifications_ns.marshal_with(success_model, code=200)
    @admin_notifications_ns.response(401, 'Unauthorized', error_model)
    @admin_notifications_ns.response(403, 'Admin access required', error_model)
    @admin_notifications_ns.response(500, 'Failed to cleanup notifications', error_model)
    @jwt_required()
    def delete(self):
        """
        Delete notifications older than the specified number of days. Admin role required.
        """
        pass


@admin_notifications_ns.route('/notifications/stats')
class AdminNotificationStats(Resource):
    @admin_notifications_ns.doc('get_global_notification_stats', security='Bearer')
    @admin_notifications_ns.param('days', 'Number of days to analyze (default: 30)', type='int')
    @admin_notifications_ns.marshal_with(success_model, code=200)
    @admin_notifications_ns.response(401, 'Unauthorized', error_model)
    @admin_notifications_ns.response(403, 'Admin access required', error_model)
    @admin_notifications_ns.response(500, 'Failed to retrieve statistics', error_model)
    @jwt_required()
    def get(self):
        """
        Retrieve global notification statistics. Admin role required.
        """
        pass
