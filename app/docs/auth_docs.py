from flask_restx import Resource
from flask import request
from app.swagger import auth_ns
from app.api_docs import (login_model, register_model, auth_response, forgot_password_model, 
                         reset_password_model, change_password_model, success_model, error_model)

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
        pass  # Implementation handled by actual auth.py route

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
        pass  # Implementation handled by actual auth.py route

@auth_ns.route('/logout')
class Logout(Resource):
    @auth_ns.doc('user_logout', security='Bearer')
    @auth_ns.marshal_with(success_model, code=200)
    @auth_ns.response(401, 'Unauthorized', error_model)
    def post(self):
        """
        User logout
        
        Invalidate the current JWT token by adding it to the blocklist.
        Requires valid JWT token in Authorization header.
        """
        pass  # Implementation handled by actual auth.py route

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
