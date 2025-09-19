from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user_model import User
from app.models.two_factor_auth_model import TwoFactorAuth, TwoFactorAttempt
from app.services.email_service import EmailService
from app.extensions import db
import pyotp
import logging

logger = logging.getLogger(__name__)
two_factor_bp = Blueprint('two_factor', __name__)

@two_factor_bp.route("/2fa/setup", methods=["POST"])
@jwt_required()
def setup_2fa():
    """Setup 2FA for user"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"status": 404, "message": "User not found"}), 404
        
        # Check if 2FA already exists
        existing_2fa = TwoFactorAuth.query.filter_by(user_id=user_id).first()
        if existing_2fa and existing_2fa.is_enabled:
            return jsonify({"status": 400, "message": "2FA is already enabled"}), 400
        
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
        
        return jsonify({
            "status": 200,
            "message": "2FA setup initiated",
            "data": {
                "qr_code": qr_code,
                "secret_key": two_fa.secret_key,
                "manual_entry_key": two_fa.secret_key
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error setting up 2FA: {str(e)}")
        return jsonify({"status": 500, "message": "Internal server error"}), 500

@two_factor_bp.route("/2fa/verify", methods=["POST"])
@jwt_required()
def verify_2fa():
    """Verify 2FA token and enable 2FA"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({"status": 400, "message": "Token is required"}), 400
        
        user_id = get_jwt_identity()
        two_fa = TwoFactorAuth.query.filter_by(user_id=user_id).first()
        
        if not two_fa:
            return jsonify({"status": 404, "message": "2FA setup not found"}), 404
        
        # Verify token
        if not two_fa.verify_token(token):
            TwoFactorAttempt.log_attempt(user_id, request.remote_addr, False, 'totp')
            return jsonify({"status": 400, "message": "Invalid token"}), 400
        
        # Enable 2FA and generate backup codes
        two_fa.is_enabled = True
        backup_codes = two_fa.generate_backup_codes()
        
        db.session.commit()
        
        # Log successful attempt
        TwoFactorAttempt.log_attempt(user_id, request.remote_addr, True, 'totp')
        
        # Send confirmation email
        user = User.query.get(user_id)
        EmailService.send_2fa_setup_email(user.email, user.name)
        
        return jsonify({
            "status": 200,
            "message": "2FA enabled successfully",
            "data": {
                "backup_codes": backup_codes
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error verifying 2FA: {str(e)}")
        return jsonify({"status": 500, "message": "Internal server error"}), 500

@two_factor_bp.route("/2fa/disable", methods=["POST"])
@jwt_required()
def disable_2fa():
    """Disable 2FA for user"""
    try:
        data = request.get_json()
        password = data.get('password')
        
        if not password:
            return jsonify({"status": 400, "message": "Password is required"}), 400
        
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.check_password(password):
            return jsonify({"status": 401, "message": "Invalid password"}), 401
        
        two_fa = TwoFactorAuth.query.filter_by(user_id=user_id).first()
        if not two_fa or not two_fa.is_enabled:
            return jsonify({"status": 400, "message": "2FA is not enabled"}), 400
        
        # Disable 2FA
        db.session.delete(two_fa)
        db.session.commit()
        
        return jsonify({
            "status": 200,
            "message": "2FA disabled successfully"
        }), 200
        
    except Exception as e:
        logger.error(f"Error disabling 2FA: {str(e)}")
        return jsonify({"status": 500, "message": "Internal server error"}), 500

@two_factor_bp.route("/2fa/status", methods=["GET"])
@jwt_required()
def get_2fa_status():
    """Get 2FA status for user"""
    try:
        user_id = get_jwt_identity()
        two_fa = TwoFactorAuth.query.filter_by(user_id=user_id).first()
        
        if not two_fa:
            return jsonify({
                "status": 200,
                "data": {
                    "enabled": False,
                    "backup_codes_remaining": 0
                }
            }), 200
        
        return jsonify({
            "status": 200,
            "data": {
                "enabled": two_fa.is_enabled,
                "backup_codes_remaining": two_fa.get_remaining_backup_codes()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting 2FA status: {str(e)}")
        return jsonify({"status": 500, "message": "Internal server error"}), 500

@two_factor_bp.route("/2fa/backup-codes", methods=["POST"])
@jwt_required()
def regenerate_backup_codes():
    """Regenerate backup codes"""
    try:
        data = request.get_json()
        password = data.get('password')
        
        if not password:
            return jsonify({"status": 400, "message": "Password is required"}), 400
        
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.check_password(password):
            return jsonify({"status": 401, "message": "Invalid password"}), 401
        
        two_fa = TwoFactorAuth.query.filter_by(user_id=user_id).first()
        if not two_fa or not two_fa.is_enabled:
            return jsonify({"status": 400, "message": "2FA is not enabled"}), 400
        
        # Generate new backup codes
        backup_codes = two_fa.generate_backup_codes()
        db.session.commit()
        
        return jsonify({
            "status": 200,
            "message": "Backup codes regenerated successfully",
            "data": {
                "backup_codes": backup_codes
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error regenerating backup codes: {str(e)}")
        return jsonify({"status": 500, "message": "Internal server error"}), 500
