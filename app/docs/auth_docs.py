from flask_restx import Resource
from flask import request, jsonify
from flask_jwt_extended import create_access_token, decode_token, get_jwt, get_jwt_identity, jwt_required
from app.swagger import auth_ns
from app.api_docs import (login_model, register_model, auth_response, forgot_password_model, 
                         reset_password_model, change_password_model, success_model, error_model)
from app.models.user_model import User
from app.models.two_factor_auth_model import TwoFactorAuth, TwoFactorAttempt
from app.services.email_service import EmailService
from app.extensions import db, BLOCKLIST
from app.schema.user_schema import User_schema
from datetime import timedelta

@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.doc('user_login')
    @auth_ns.expect(login_model)
    @auth_ns.marshal_with(auth_response, code=200)
    @auth_ns.response(401, 'Invalid credentials', error_model)
    @auth_ns.response(400, 'Invalid data', error_model)
    def post(self):
        """
        User login
        
        Authenticate user with email and password to receive JWT access token.
        The token should be included in subsequent requests as: Authorization: Bearer {token}
        """
        data = request.get_json()
        user = User.query.filter_by(email=data.get("email")).first()

        if not user or not user.check_password(data.get("password")):
            return {"status": 401, "message": "Invalid credentials"}, 401

        # Check if 2FA is enabled
        two_fa = TwoFactorAuth.query.filter_by(user_id=str(user.id)).first()
        if two_fa and two_fa.is_enabled:
            # Check for 2FA token
            two_fa_token = data.get("two_fa_token")
            backup_code = data.get("backup_code")
            
            if not two_fa_token and not backup_code:
                return {
                    "status": 200,
                    "message": "2FA required",
                    "requires_2fa": True
                }, 200
            
            # Check rate limiting
            failed_attempts = TwoFactorAttempt.get_recent_failed_attempts(str(user.id))
            if failed_attempts >= 5:
                return {
                    "status": 429,
                    "message": "Too many failed 2FA attempts. Please try again later."
                }, 429
            
            # Verify 2FA token or backup code
            if two_fa_token:
                if not two_fa.verify_token(two_fa_token):
                    TwoFactorAttempt.log_attempt(str(user.id), request.remote_addr, False, 'totp')
                    return {"status": 401, "message": "Invalid 2FA token"}, 401
                TwoFactorAttempt.log_attempt(str(user.id), request.remote_addr, True, 'totp')
            elif backup_code:
                if not two_fa.verify_backup_code(backup_code):
                    TwoFactorAttempt.log_attempt(str(user.id), request.remote_addr, False, 'backup_code')
                    return {"status": 401, "message": "Invalid backup code"}, 401
                TwoFactorAttempt.log_attempt(str(user.id), request.remote_addr, True, 'backup_code')
                db.session.commit()  # Save backup code usage

        access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role}, expires_delta=timedelta(days=1))
        
        # Send login notification email
        try:
            EmailService.send_login_notification(user.email, user.name, request.remote_addr)
        except Exception as e:
            # Don't fail login if email fails
            pass

        user_schema = User_schema()
        return {
            "status": 200,
            "message": "Login successful",
            "data": {
                "access_token": access_token,
                "user": user_schema.dump(user)
            }
        }, 200

@auth_ns.route('/register')
class Register(Resource):
    @auth_ns.doc('user_register')
    @auth_ns.expect(register_model)
    @auth_ns.marshal_with(auth_response, code=201)
    @auth_ns.response(409, 'User already exists', error_model)
    @auth_ns.response(400, 'Invalid data', error_model)
    def post(self):
        """
        User registration
        
        Create a new user account with email, password and profile information.
        Returns JWT access token for immediate authentication.
        """
        data = request.get_json()
        try:
            user_schema = User_schema()
            user = user_schema.load(data)
        except Exception as e:
            return {"status": 400, "message": "Invalid data", "error": str(e)}, 400

        if User.query.filter_by(email=user.email).first():
            return {"status": 409, "message": "User already exists"}, 409

        db.session.add(user)
        db.session.commit()

        access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role}, expires_delta=timedelta(days=1))

        user_schema = User_schema()
        return {
            "status": 201,
            "message": "User created successfully",
            "data": {
                "token": access_token,
                "user": user_schema.dump(user)
            }
        }, 201

@auth_ns.route('/logout')
class Logout(Resource):
    @auth_ns.doc('user_logout', security='Bearer')
    @auth_ns.marshal_with(success_model, code=200)
    @auth_ns.response(401, 'Unauthorized', error_model)
    @jwt_required()
    def post(self):
        """
        User logout
        
        Invalidate the current JWT token by adding it to the blocklist.
        Requires valid JWT token in Authorization header.
        """
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"status": 200, "message": "Successfully logged out"}, 200

@auth_ns.route('/forgot')
class ForgotPassword(Resource):
    @auth_ns.doc('forgot_password')
    @auth_ns.expect(forgot_password_model)
    @auth_ns.marshal_with(success_model, code=200)
    @auth_ns.response(400, 'Invalid data', error_model)
    def post(self):
        """
        Forgot password
        
        Generate a password reset token for the user.
        Returns success message regardless of whether user exists (security measure).
        """
        pass  # Implementation handled by actual auth.py route

@auth_ns.route('/reset')
class ResetPassword(Resource):
    @auth_ns.doc('reset_password')
    @auth_ns.expect(reset_password_model)
    @auth_ns.marshal_with(success_model, code=200)
    @auth_ns.response(400, 'Invalid or expired token', error_model)
    @auth_ns.response(404, 'User not found', error_model)
    def post(self):
        """
        Reset password
        
        Reset user password using the reset token from forgot password endpoint.
        The reset token expires after 1 hour.
        """
        pass  # Implementation handled by actual auth.py route

@auth_ns.route('/change_password')
class ChangePassword(Resource):
    @auth_ns.doc('change_password', security='Bearer')
    @auth_ns.expect(change_password_model)
    @auth_ns.marshal_with(success_model, code=200)
    @auth_ns.response(400, 'Invalid data', error_model)
    @auth_ns.response(401, 'Current password incorrect or unauthorized', error_model)
    def post(self):
        """
        Change password
        
        Change user password when authenticated.
        Requires current password for verification and new password cannot be the same.
        """
        pass  # Implementation handled by actual auth.py route
