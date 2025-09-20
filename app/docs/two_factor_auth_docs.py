from flask_restx import Resource, fields
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.swagger import api
from app.api_docs import success_model, error_model
from app.models.user_model import User
from app.models.two_factor_auth_model import TwoFactorAuth, TwoFactorAttempt
from app.services.email_service import EmailService
from app.extensions import db
import logging
import pyotp

logger = logging.getLogger(__name__)

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
    @jwt_required()
    def post(self):
        """Setup Two-Factor Authentication
        
        Generates a new TOTP secret key and QR code for setting up 2FA.
        Returns the secret key, QR code image, and initial backup codes.
        """
        try:
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user:
                return {"status": 404, "message": "User not found"}, 404
            
            # Check if 2FA already exists
            existing_2fa = TwoFactorAuth.query.filter_by(user_id=user_id).first()
            if existing_2fa and existing_2fa.is_enabled:
                return {"status": 400, "message": "2FA is already enabled"}, 400
            
            # Create or update 2FA record
            if existing_2fa:
                two_fa = existing_2fa
                two_fa.secret_key = pyotp.random_base32()  # Generate new secret
            else:
                two_fa = TwoFactorAuth(user_id=user_id)
                db.session.add(two_fa)
            
            # Generate QR code
            qr_code = two_fa.get_qr_code(user.email)
            
            db.session.commit()
            
            return {
                "status": 200,
                "message": "2FA setup initiated",
                "data": {
                    "qr_code": qr_code,
                    "secret_key": two_fa.secret_key,
                    "manual_entry_key": two_fa.secret_key
                }
            }, 200
            
        except Exception as e:
            logger.error(f"Error setting up 2FA: {str(e)}")
            return {"status": 500, "message": "Internal server error"}, 500

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
    @jwt_required()
    def get(self):
        """Get Two-Factor Authentication Status
        
        Returns the current 2FA status and remaining backup codes count.
        """
        try:
            user_id = get_jwt_identity()
            two_fa = TwoFactorAuth.query.filter_by(user_id=user_id).first()
            
            if not two_fa:
                return {
                    "status": 200,
                    "data": {
                        "enabled": False,
                        "backup_codes_remaining": 0
                    }
                }, 200
            
            return {
                "status": 200,
                "data": {
                    "enabled": two_fa.is_enabled,
                    "backup_codes_remaining": two_fa.get_remaining_backup_codes()
                }
            }, 200
            
        except Exception as e:
            logger.error(f"Error getting 2FA status: {str(e)}")
            return {"status": 500, "message": "Internal server error"}, 500

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
