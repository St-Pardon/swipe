from flask_restx import Resource, fields
from app.swagger import api
from app.api_docs import success_model, error_model

# Create namespace for 2FA
two_factor_ns = api.namespace('2fa', description='Two-Factor Authentication operations')

# 2FA Models
two_factor_setup_response = api.model('TwoFactorSetupResponse', {
    'secret_key': fields.String(description='Base32 secret key for TOTP'),
    'qr_code': fields.String(description='Base64 encoded QR code image'),
    'backup_codes': fields.List(fields.String, description='List of backup codes')
})

two_factor_verify_request = api.model('TwoFactorVerifyRequest', {
    'token': fields.String(required=True, description='6-digit TOTP token', example='123456')
})

two_factor_disable_request = api.model('TwoFactorDisableRequest', {
    'password': fields.String(required=True, description='Current user password')
})

two_factor_status_response = api.model('TwoFactorStatusResponse', {
    'is_enabled': fields.Boolean(description='Whether 2FA is enabled'),
    'backup_codes_remaining': fields.Integer(description='Number of backup codes remaining')
})

backup_codes_response = api.model('BackupCodesResponse', {
    'backup_codes': fields.List(fields.String, description='New list of backup codes')
})

@two_factor_ns.route('/setup')
class TwoFactorSetup(Resource):
    @api.doc('setup_2fa')
    @api.marshal_with(success_model)
    @api.response(200, 'Success', success_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(401, 'Unauthorized', error_model)
    @api.response(409, 'Conflict - 2FA already enabled', error_model)
    def post(self):
        """Setup Two-Factor Authentication
        
        Generates a new TOTP secret key and QR code for setting up 2FA.
        Returns the secret key, QR code image, and initial backup codes.
        """
        pass

@two_factor_ns.route('/verify')
class TwoFactorVerify(Resource):
    @api.doc('verify_2fa')
    @api.expect(two_factor_verify_request)
    @api.marshal_with(success_model)
    @api.response(200, 'Success - 2FA enabled', success_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(401, 'Unauthorized', error_model)
    @api.response(409, 'Conflict - 2FA already enabled', error_model)
    @api.response(429, 'Too Many Requests', error_model)
    def post(self):
        """Verify and Enable Two-Factor Authentication
        
        Verifies the TOTP token and enables 2FA for the user account.
        Also sends a confirmation email to the user.
        """
        pass

@two_factor_ns.route('/disable')
class TwoFactorDisable(Resource):
    @api.doc('disable_2fa')
    @api.expect(two_factor_disable_request)
    @api.marshal_with(success_model)
    @api.response(200, 'Success - 2FA disabled', success_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(401, 'Unauthorized', error_model)
    @api.response(404, 'Not Found - 2FA not enabled', error_model)
    def post(self):
        """Disable Two-Factor Authentication
        
        Disables 2FA for the user account after password verification.
        Requires the user's current password for security.
        """
        pass

@two_factor_ns.route('/status')
class TwoFactorStatus(Resource):
    @api.doc('get_2fa_status')
    @api.marshal_with(success_model)
    @api.response(200, 'Success', success_model)
    @api.response(401, 'Unauthorized', error_model)
    def get(self):
        """Get Two-Factor Authentication Status
        
        Returns the current 2FA status and remaining backup codes count.
        """
        pass

@two_factor_ns.route('/backup-codes/regenerate')
class TwoFactorBackupCodes(Resource):
    @api.doc('regenerate_backup_codes')
    @api.marshal_with(success_model)
    @api.response(200, 'Success', success_model)
    @api.response(401, 'Unauthorized', error_model)
    @api.response(404, 'Not Found - 2FA not enabled', error_model)
    def post(self):
        """Regenerate Backup Codes
        
        Generates new backup codes for 2FA, replacing all existing codes.
        Returns the new list of backup codes.
        """
        pass
