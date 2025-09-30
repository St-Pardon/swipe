from flask_restx import fields
from app.swagger import api

# Authentication Models
login_model = api.model('Login', {
    'email': fields.String(required=True, description='User email address', example='john.doe@example.com'),
    'password': fields.String(required=True, description='User password', example='password123')
})

register_model = api.model('Register', {
    'name': fields.String(required=True, description='Full name', example='John Doe'),
    'email': fields.String(required=True, description='User email address', example='john.doe@example.com'),
    'password': fields.String(required=True, description='User password', example='password123'),
    'phone': fields.String(description='Phone number', example='+1234567890'),
    'address': fields.String(description='Street address', example='123 Main St, New York, NY'),
    'city': fields.String(description='City', example='New York'),
    'country': fields.String(description='Country', example='United States'),
    'countryCode': fields.String(description='Country code', example='US')
})

auth_response = api.model('AuthResponse', {
    'status': fields.Integer(description='HTTP status code', example=200),
    'message': fields.String(description='Response message', example='Login successful'),
    'data': fields.Raw(description='Response data containing token and user info')
})

forgot_password_model = api.model('ForgotPassword', {
    'email': fields.String(required=True, description='User email address', example='john.doe@example.com')
})

reset_password_model = api.model('ResetPassword', {
    'reset_token': fields.String(required=True, description='Password reset token'),
    'password': fields.String(required=True, description='New password', example='newpassword123')
})

change_password_model = api.model('ChangePassword', {
    'current_password': fields.String(required=True, description='Current password', example='oldpassword123'),
    'new_password': fields.String(required=True, description='New password', example='newpassword123')
})

# User Models
user_model = api.model('User', {
    'id': fields.String(description='User ID'),
    'name': fields.String(description='User full name'),
    'email': fields.String(description='User email address'),
    'phone': fields.String(description='Phone number'),
    'address': fields.String(description='Street address'),
    'city': fields.String(description='City'),
    'country': fields.String(description='Country'),
    'countryCode': fields.String(description='Country code'),
    'role': fields.String(description='User role'),
    'email_verified': fields.Boolean(description='Email verification status'),
    'created_at': fields.String(description='Creation timestamp'),
    'updated_at': fields.String(description='Last update timestamp')
})

user_update_model = api.model('UserUpdate', {
    'name': fields.String(description='User full name', example='John Updated'),
    'phone': fields.String(description='Phone number', example='+1234567891'),
    'address': fields.String(description='Street address', example='456 Updated St, New York, NY'),
    'city': fields.String(description='City', example='New York'),
    'country': fields.String(description='Country', example='United States'),
    'countryCode': fields.String(description='Country code', example='US'),
    'password': fields.String(description='New password (optional)', example='newpassword123')
})

# Beneficiary Models
beneficiary_model = api.model('Beneficiary', {
    'id': fields.String(description='Beneficiary ID'),
    'beneficiary_name': fields.String(description='Beneficiary name'),
    'account_number': fields.String(description='Account number'),
    'routing_number': fields.String(description='Routing number'),
    'bank_name': fields.String(description='Bank name'),
    'account_type': fields.String(description='Account type'),
    'created_at': fields.String(description='Creation timestamp')
})

beneficiary_create_model = api.model('BeneficiaryCreate', {
    'beneficiary_name': fields.String(required=True, description='Beneficiary name', example='Jane Smith'),
    'account_number': fields.String(required=True, description='Account number', example='1234567890'),
    'routing_number': fields.String(required=True, description='Routing number', example='021000021'),
    'bank_name': fields.String(required=True, description='Bank name', example='Chase Bank'),
    'account_type': fields.String(description='Account type', example='checking')
})

# Virtual Card Models
virtual_card_model = api.model('VirtualCard', {
    'id': fields.String(description='Card ID'),
    'card_number': fields.String(description='Masked card number'),
    'card_holder_name': fields.String(description='Card holder name'),
    'expiry_month': fields.Integer(description='Expiry month'),
    'expiry_year': fields.Integer(description='Expiry year'),
    'cvv': fields.String(description='CVV'),
    'card_type': fields.String(description='Card type'),
    'status': fields.String(description='Card status'),
    'spending_limit': fields.Float(description='Spending limit'),
    'balance': fields.Float(description='Card balance'),
    'created_at': fields.String(description='Creation timestamp')
})

virtual_card_create_model = api.model('VirtualCardCreate', {
    'account_id': fields.String(required=True, description='Associated account ID'),
    'card_type': fields.String(description='Card type', example='debit'),
    'spending_limit': fields.Float(description='Spending limit', example=1000.00)
})

# Card Payment Models
card_fund_wallet_model = api.model('CardFundWallet', {
    'amount': fields.Float(required=True, description='Amount to fund', example=100.00),
    'currency': fields.String(description='Currency code', example='USD'),
    'description': fields.String(description='Payment description', example='Fund wallet via card')
})

# Account Models
account_model = api.model('Account', {
    'id': fields.String(description='Account ID'),
    'account_number': fields.String(description='Account number'),
    'account_number_masked': fields.String(description='Masked account number'),
    'balance': fields.Float(description='Account balance'),
    'currency': fields.String(description='Currency code'),
    'currency_code': fields.String(description='Currency code'),
    'bank_name': fields.String(description='Bank name'),
    'account_holder': fields.String(description='Account holder name'),
    'routing_number': fields.String(description='Routing number'),
    'accountType': fields.String(description='Account type'),
    'address': fields.String(description='Account address'),
    'is_default': fields.Boolean(description='Is default account'),
    'created_at': fields.String(description='Creation timestamp'),
    'updated_at': fields.String(description='Last update timestamp'),
    'user': fields.Nested(user_model, description='Account owner')
})

account_create_model = api.model('AccountCreate', {
    'account_number': fields.String(required=True, description='Account number', example='1234567890'),
    'routing_number': fields.String(required=True, description='Routing number', example='021000021'),
    'bank_name': fields.String(required=True, description='Bank name', example='Chase Bank'),
    'account_holder': fields.String(required=True, description='Account holder name', example='John Doe'),
    'accountType': fields.String(description='Account type', example='checking'),
    'address': fields.String(description='Account address', example='123 Main St, New York, NY'),
    'currency': fields.String(description='Currency code', example='USD'),
    'is_default': fields.Boolean(description='Set as default account', example=False)
})

# Transfer Models
transfer_model = api.model('Transfer', {
    'amount': fields.Float(required=True, description='Transfer amount', example=50.00),
    'currency': fields.String(required=True, description='Currency code', example='USD'),
    'transfer_type': fields.String(required=True, description='Transfer type', 
                                 enum=['beneficiary', 'internal', 'customer', 'external'],
                                 example='internal'),
    'source_account_id': fields.String(description='Source account ID'),
    'target_account_id': fields.String(description='Target account ID (for internal transfers)'),
    'beneficiary_id': fields.String(description='Beneficiary ID (for beneficiary transfers)'),
    'target_user_email': fields.String(description='Target user email (for customer transfers)'),
    'target_account_number': fields.String(description='Target account number'),
    'target_routing_number': fields.String(description='Target routing number (for external transfers)'),
    'target_bank_name': fields.String(description='Target bank name (for external transfers)'),
    'target_account_holder': fields.String(description='Target account holder name (for external transfers)'),
    'description': fields.String(description='Transfer description', example='Internal transfer between accounts')
})

transfer_response = api.model('TransferResponse', {
    'status': fields.Integer(description='HTTP status code', example=201),
    'message': fields.String(description='Response message', example='Transfer initiated successfully'),
    'data': fields.Raw(description='Transfer details')
})

# Withdrawal Models
withdrawal_model = api.model('Withdrawal', {
    'amount': fields.Float(required=True, description='Withdrawal amount', example=20.00),
    'currency': fields.String(required=True, description='Currency code', example='USD'),
    'account_number': fields.String(required=True, description='Target account number', example='2025873081'),
    'account_id': fields.String(description='Source account ID'),
    'description': fields.String(description='Withdrawal description', example='Withdrawal to external bank account')
})

# Error Models
error_model = api.model('Error', {
    'status': fields.Integer(description='HTTP status code'),
    'message': fields.String(description='Error message'),
    'errors': fields.Raw(description='Detailed error information')
})

# Transaction Models
transaction_model = api.model('Transaction', {
    'id': fields.String(description='Transaction ID'),
    'type': fields.String(description='Transaction type'),
    'status': fields.String(description='Transaction status'),
    'amount': fields.Float(description='Transaction amount'),
    'currency_code': fields.String(description='Currency code'),
    'description': fields.String(description='Transaction description'),
    'created_at': fields.String(description='Creation timestamp'),
    'updated_at': fields.String(description='Last update timestamp')
})

# Pagination Models
pagination_model = api.model('Pagination', {
    'page': fields.Integer(description='Current page number'),
    'size': fields.Integer(description='Items per page'),
    'total': fields.Integer(description='Total number of items'),
    'pages': fields.Integer(description='Total number of pages')
})

# Success Models
success_model = api.model('Success', {
    'status': fields.Integer(description='HTTP status code'),
    'message': fields.String(description='Success message'),
    'data': fields.Raw(description='Response data')
})

success_with_pagination = api.model('SuccessWithPagination', {
    'status': fields.Integer(description='HTTP status code'),
    'message': fields.String(description='Success message'),
    'data': fields.Raw(description='Response data'),
    'pagination': fields.Nested(pagination_model, description='Pagination information')
})

# Notification Models
notification_detail_model = api.model('NotificationDetail', {
    'id': fields.String(description='Notification ID', example='9d35d1bf-8aea-4fca-9c77-6ad0f3a7b653'),
    'user_id': fields.String(description='Owner user ID', example='a3e2e7ff-94e4-4a2a-b3f9-413b5ddbadc0'),
    'title': fields.String(description='Notification title', example='Wallet funding complete'),
    'message': fields.String(description='Detailed notification message'),
    'category': fields.String(description='Notification category', example='transaction'),
    'priority': fields.String(description='Priority level', example='high'),
    'is_read': fields.Boolean(description='Read status flag'),
    'read_at': fields.String(description='Timestamp when notification was read', example='2024-02-10T14:30:00Z'),
    'metadata': fields.Raw(description='Additional metadata payload'),
    'created_at': fields.String(description='Creation timestamp', example='2024-02-10T14:25:00Z'),
    'updated_at': fields.String(description='Last update timestamp', example='2024-02-10T14:25:00Z')
})

notification_toggle_request = api.model('NotificationToggleRequest', {
    'is_read': fields.Boolean(required=False, description='Mark notification as read (true) or unread (false)', example=True)
})

notification_bulk_toggle_request = api.model('NotificationBulkToggleRequest', {
    'notification_ids': fields.List(fields.String, required=True, description='List of notification IDs to update'),
    'is_read': fields.Boolean(required=False, description='Read state to apply to the notifications', example=True)
})

notification_clear_params = api.model('NotificationClearParams', {
    'category': fields.String(description='Filter notifications by category before clearing', example='system'),
    'older_than': fields.String(description='ISO timestamp; clear notifications created before this time', example='2024-01-01T00:00:00Z'),
    'status': fields.String(description='Filter by status before clearing', enum=['read', 'unread'], example='read')
})

notification_settings_model = api.model('NotificationSettings', {
    'id': fields.String(description='Notification settings ID'),
    'user_id': fields.String(description='Owner user ID'),
    'email_security': fields.Boolean(description='Receive security notifications via email'),
    'email_transaction': fields.Boolean(description='Receive transaction notifications via email'),
    'email_system': fields.Boolean(description='Receive system notifications via email'),
    'email_marketing': fields.Boolean(description='Receive marketing notifications via email'),
    'in_app_security': fields.Boolean(description='Receive security notifications in app'),
    'in_app_transaction': fields.Boolean(description='Receive transaction notifications in app'),
    'in_app_system': fields.Boolean(description='Receive system notifications in app'),
    'in_app_marketing': fields.Boolean(description='Receive marketing notifications in app'),
    'push_enabled': fields.Boolean(description='Receive push notifications'),
    'push_security': fields.Boolean(description='Enable push security notifications'),
    'push_transaction': fields.Boolean(description='Enable push transaction notifications'),
    'push_system': fields.Boolean(description='Enable push system notifications'),
    'quiet_hours_start': fields.String(description='Quiet hours start time (HH:MM)', example='22:00'),
    'quiet_hours_end': fields.String(description='Quiet hours end time (HH:MM)', example='06:00'),
    'quiet_hours_enabled': fields.Boolean(description='Enable quiet hours for notifications'),
    'created_at': fields.String(description='Creation timestamp'),
    'updated_at': fields.String(description='Last update timestamp')
})

notification_settings_update_model = api.model('NotificationSettingsUpdate', {
    'email_security': fields.Boolean(description='Toggle security notification emails'),
    'email_transaction': fields.Boolean(description='Toggle transaction notification emails'),
    'email_system': fields.Boolean(description='Toggle system notification emails'),
    'email_marketing': fields.Boolean(description='Toggle marketing notification emails'),
    'in_app_security': fields.Boolean(description='Toggle in-app security notifications'),
    'in_app_transaction': fields.Boolean(description='Toggle in-app transaction notifications'),
    'in_app_system': fields.Boolean(description='Toggle in-app system notifications'),
    'in_app_marketing': fields.Boolean(description='Toggle in-app marketing notifications'),
    'push_enabled': fields.Boolean(description='Toggle push notifications globally'),
    'push_security': fields.Boolean(description='Toggle push security notifications'),
    'push_transaction': fields.Boolean(description='Toggle push transaction notifications'),
    'push_system': fields.Boolean(description='Toggle push system notifications'),
    'quiet_hours_start': fields.String(description='Quiet hours start (HH:MM)', example='21:00'),
    'quiet_hours_end': fields.String(description='Quiet hours end (HH:MM)', example='07:00'),
    'quiet_hours_enabled': fields.Boolean(description='Enable or disable quiet hours')
})

broadcast_notification_model = api.model('BroadcastNotificationRequest', {
    'title': fields.String(required=True, description='Notification title', example='Scheduled maintenance'),
    'message': fields.String(required=True, description='Notification message body'),
    'category': fields.String(description='Notification category', example='system'),
    'priority': fields.String(description='Notification priority', example='medium'),
    'notification_types': fields.List(fields.String, description='Channels to use (in_app, email, push)'),
    'target_users': fields.String(description="Audience selector ('all', 'verified', 'active')", example='all'),
    'user_filters': fields.Raw(description='Optional filter dictionary for advanced targeting'),
    'metadata': fields.Raw(description='Additional metadata payload to attach to notifications')
})

notification_payload_model = api.model('NotificationPayload', {
    'title': fields.String(required=True, description='Notification title', example='Balance low'),
    'message': fields.String(required=True, description='Notification message body'),
    'category': fields.String(description='Notification category', example='transaction'),
    'priority': fields.String(description='Notification priority', example='high'),
    'metadata': fields.Raw(description='Additional metadata payload')
})

bulk_notification_request_model = api.model('BulkNotificationRequest', {
    'user_ids': fields.List(fields.String, required=True, description='List of user IDs to target'),
    'notifications': fields.List(fields.Nested(notification_payload_model), required=True, description='Notifications to create for each user')
})
