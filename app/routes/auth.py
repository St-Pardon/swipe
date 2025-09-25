from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, decode_token, get_jwt, get_jwt_identity, jwt_required
from app.models.user_model import User
from app.models.two_factor_auth_model import TwoFactorAuth, TwoFactorAttempt
from app.models.notification_model import Notification, NotificationSettings
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService
from app.extensions import db, BLOCKLIST
from app.schema.user_schema import User_schema
from datetime import timedelta


auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    try:
        user_schema = User_schema()
        user = user_schema.load(data)
    except Exception as e:
        return jsonify({"status": 400,
                        "message": "Invalid data",
                        "error": str(e)}), 400

    if User.query.filter_by(email=user.email).first():
        return jsonify({"status": 409,
                        "message": "User already exists"}), 409

    # Generate email verification token
    verification_token = user.generate_email_verification_token()

    db.session.add(user)
    db.session.commit()

    # Create default notification settings for new user
    default_settings = NotificationSettings.create_default_settings(user.id)
    db.session.add(default_settings)

    # Send welcome notification via both in-app and email
    welcome_notification = Notification(
        user_id=user.id,
        title="Welcome to Swipe Payment!",
        message="Your account has been created successfully. You can now send and receive payments.",
        category="system",
        priority="medium"
    )
    db.session.add(welcome_notification)

    # Send verification email
    EmailService.send_verification_email(
        user.email,
        user.name,
        verification_token
    )

    db.session.commit()

    user_schema = User_schema()
    return jsonify({"status": 201,
                    "message": "User created successfully. Please check your email to verify your account.",
                    "data": {
                        "user": user_schema.dump(user),
                        "email_verification_required": True
                    }}), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get("email")).first()

    if not user or not user.check_password(data.get("password")):
        return jsonify({"status": 401,
                        "message": "Invalid credentials"}), 401

    # Check if email is verified
    if not user.email_verified:
        return jsonify({"status": 403,
                        "message": "Email not verified. Please check your email for verification instructions."}), 403

    # Check if 2FA is enabled
    two_fa = TwoFactorAuth.query.filter_by(user_id=str(user.id)).first()
    if two_fa and two_fa.is_enabled:
        # Check for 2FA token
        two_fa_token = data.get("two_fa_token")
        backup_code = data.get("backup_code")
        
        if not two_fa_token and not backup_code:
            return jsonify({
                "status": 200,
                "message": "2FA required",
                "requires_2fa": True
            }), 200
        
        # Check rate limiting
        failed_attempts = TwoFactorAttempt.get_recent_failed_attempts(str(user.id))
        if failed_attempts >= 5:
            return jsonify({
                "status": 429,
                "message": "Too many failed 2FA attempts. Please try again later."
            }), 429
        
        # Verify 2FA token or backup code
        if two_fa_token:
            if not two_fa.verify_token(two_fa_token):
                TwoFactorAttempt.log_attempt(str(user.id), request.remote_addr, False, 'totp')
                return jsonify({"status": 401, "message": "Invalid 2FA token"}), 401
            TwoFactorAttempt.log_attempt(str(user.id), request.remote_addr, True, 'totp')
        elif backup_code:
            if not two_fa.verify_backup_code(backup_code):
                TwoFactorAttempt.log_attempt(str(user.id), request.remote_addr, False, 'backup_code')
                return jsonify({"status": 401, "message": "Invalid backup code"}), 401
            TwoFactorAttempt.log_attempt(str(user.id), request.remote_addr, True, 'backup_code')

    # Send login notification email
    EmailService.send_login_notification_email(
        user.email, 
        user.name, 
        request.remote_addr or "Unknown"
    )

    access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role}, expires_delta=timedelta(days=1))

    user_schema = User_schema()
    return jsonify({"status": 200,
                    "message": "Login successful",
                    "data": {
                        "token":access_token,
                        "user": user_schema.dump(user)
                    }})

@auth_bp.route("/verify-email", methods=["GET"])
def verify_email():
    token = request.args.get("token")

    if not token:
        return jsonify({"status": 400,
                        "message": "Verification token is required"}), 400

    # Find user by verification token
    user = User.query.filter_by(email_verification_token=token).first()

    if not user:
        return jsonify({"status": 404,
                        "message": "Invalid or expired verification token"}), 404

    # Verify the token and mark email as verified
    if user.verify_email_token(token):
        user.mark_email_verified()
        db.session.commit()

        # Generate access token for immediate login
        access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role}, expires_delta=timedelta(days=1))

        user_schema = User_schema()
        return jsonify({"status": 200,
                        "message": "Email verified successfully. Welcome to Swipe Payment!",
                        "data": {
                            "token": access_token,
                            "user": user_schema.dump(user)
                        }}), 200
    else:
        return jsonify({"status": 400,
                        "message": "Invalid verification token"}), 400

@auth_bp.route("/resend-verification", methods=["POST"])
def resend_verification():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"status": 400,
                        "message": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"status": 404,
                        "message": "User not found"}), 404

    if user.email_verified:
        return jsonify({"status": 400,
                        "message": "Email is already verified"}), 400

    # Generate new verification token
    verification_token = user.generate_email_verification_token()
    db.session.commit()

    # Send verification email
    success = EmailService.send_verification_email(
        user.email,
        user.name,
        verification_token
    )

    if success:
        return jsonify({"status": 200,
                        "message": "Verification email sent successfully"}), 200
    else:
        return jsonify({"status": 500,
                        "message": "Failed to send verification email. Please try again later."}), 500

@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    BLOCKLIST.add(jti)
    return jsonify({"status": 200, "message": "Successfully logged out"}), 200

@auth_bp.route("/forgot", methods=["POST"])
def forgot():
    data = request.get_json()
    email = data.get("email")

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"status": 200,
                        "message": "If a user exists, a password reset link has been sent."}), 200

    # Generate a time-sensitive, stateless reset token
    reset_token = create_access_token(
        identity=str(user.id),
        expires_delta=timedelta(hours=1), # The token expires in 1 hour
        additional_claims={"type": "password_reset"}
    )
    
    # Send password reset email
    EmailService.send_password_reset_email(user.email, reset_token)
    
    return jsonify({"status": 200,
                    "message": "If a user exists, a password reset link has been sent."}), 200


@auth_bp.route("/reset", methods=["POST"])
def reset():
    data = request.get_json()
    reset_token = data.get("reset_token")
    new_password = data.get("password")

    if not reset_token:
        return jsonify({"status": 400, "message": "Reset token is required"}), 400
    
    if not new_password:
        return jsonify({"status": 400, "message": "New password is required"}), 400

    try:
        decoded = decode_token(reset_token) 
        user_id = decoded["sub"] # extract user id from jwt
        claims = decoded.get("type")

        if claims != "password_reset":
            return jsonify({"status": 400, "message": "Invalid token type"}), 400

    except Exception as e:
        return jsonify({"status": 400, "message": "Invalid or expired token"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"status": 404, "message": "User not found"}), 404

    user.set_password(new_password)
    db.session.commit()

    return jsonify({"status": 200, "message": "Password reset successful"}), 200


@auth_bp.route("/change_password", methods=["POST"])
@jwt_required()
def change_password():
    data = request.get_json()
    current_password = data.get("current_password")
    new_password = data.get("new_password")

    if not current_password or not new_password:
        return jsonify({"status": 400, "message": "Current password and new password are required"}), 400

    current_user = User.query.get(get_jwt_identity())
    if not current_user.check_password(current_password):
        return jsonify({"status": 401, "message": "Current password is incorrect"}), 401

    if current_password == new_password:
        return jsonify({"status": 400, "message": "New password cannot be the same as the current password"}), 400

    current_user.set_password(new_password)
    db.session.commit()

    return jsonify({"status": 200, "message": "Password changed successfully"}), 200
