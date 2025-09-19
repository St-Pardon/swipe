from flask_restx import Resource
from flask import request
from app.swagger import users_ns
from app.api_docs import (user_model, user_update_model, beneficiary_model, beneficiary_create_model, 
                         success_model, success_with_pagination, error_model)

@users_ns.route('/users')
class UsersList(Resource):
    @users_ns.doc('get_users', security='Bearer')
    @users_ns.marshal_list_with(user_model, code=200)
    @users_ns.response(401, 'Unauthorized', error_model)
    @users_ns.response(500, 'Internal server error', error_model)
    def get(self):
        """
        Get all users
        
        Retrieve all users in the system. Requires authentication.
        """
        pass  # Implementation handled by actual users.py route

@users_ns.route('/user')
class UserDetail(Resource):
    @users_ns.doc('get_user', security='Bearer')
    @users_ns.param('id', 'User ID (optional, defaults to current user)', type='string', required=False)
    @users_ns.marshal_with(success_model, code=200)
    @users_ns.response(401, 'Unauthorized', error_model)
    @users_ns.response(404, 'User not found', error_model)
    @users_ns.response(500, 'Internal server error', error_model)
    def get(self):
        """
        Get user details
        
        Retrieve details of a specific user by ID, or current authenticated user if no ID provided.
        """
        pass  # Implementation handled by actual users.py route

    @users_ns.doc('update_user', security='Bearer')
    @users_ns.param('id', 'User ID (optional, defaults to current user)', type='string', required=False)
    @users_ns.expect(user_update_model)
    @users_ns.marshal_with(success_model, code=200)
    @users_ns.response(400, 'Invalid data or validation error', error_model)
    @users_ns.response(401, 'Unauthorized', error_model)
    @users_ns.response(404, 'User not found', error_model)
    @users_ns.response(500, 'Internal server error', error_model)
    def put(self):
        """
        Update user information
        
        Update user profile information. All fields are optional.
        Password will be hashed if provided.
        """
        pass  # Implementation handled by actual users.py route

    @users_ns.doc('delete_user', security='Bearer')
    @users_ns.param('id', 'User ID (optional, defaults to current user)', type='string', required=False)
    @users_ns.marshal_with(success_model, code=200)
    @users_ns.response(401, 'Unauthorized', error_model)
    @users_ns.response(404, 'User not found', error_model)
    @users_ns.response(500, 'Internal server error', error_model)
    def delete(self):
        """
        Delete user
        
        Delete a user account. If no ID provided, deletes current authenticated user.
        """
        pass  # Implementation handled by actual users.py route

@users_ns.route('/user/<string:id>/beneficiaries')
class UserBeneficiaries(Resource):
    @users_ns.doc('get_beneficiaries', security='Bearer')
    @users_ns.param('page', 'Page number (default: 0)', type='int', required=False)
    @users_ns.param('size', 'Items per page (default: 10)', type='int', required=False)
    @users_ns.param('search', 'Search term for beneficiary name, bank name, or account number', type='string', required=False)
    @users_ns.marshal_with(success_with_pagination, code=200)
    @users_ns.response(401, 'Unauthorized', error_model)
    @users_ns.response(500, 'Internal server error', error_model)
    def get(self, id):
        """
        Get user beneficiaries
        
        Retrieve paginated list of beneficiaries for a user with optional search functionality.
        Supports searching by beneficiary name, bank name, or account number.
        """
        pass  # Implementation handled by actual users.py route

    @users_ns.doc('create_beneficiary', security='Bearer')
    @users_ns.expect(beneficiary_create_model)
    @users_ns.marshal_with(success_model, code=201)
    @users_ns.response(400, 'Invalid data or validation error', error_model)
    @users_ns.response(401, 'Unauthorized', error_model)
    @users_ns.response(500, 'Internal server error', error_model)
    def post(self, id):
        """
        Create beneficiary
        
        Add a new beneficiary for the authenticated user.
        All bank details are required for external transfers.
        """
        pass  # Implementation handled by actual users.py route

@users_ns.route('/user/<string:id>/beneficiaries/<string:beneficiary_id>')
class UserBeneficiaryDetail(Resource):
    @users_ns.doc('get_beneficiary', security='Bearer')
    @users_ns.marshal_with(success_model, code=200)
    @users_ns.response(401, 'Unauthorized', error_model)
    @users_ns.response(404, 'Beneficiary not found', error_model)
    @users_ns.response(500, 'Internal server error', error_model)
    def get(self, id, beneficiary_id):
        """
        Get beneficiary details
        
        Retrieve details of a specific beneficiary by ID.
        """
        pass  # Implementation handled by actual users.py route

@users_ns.route('/beneficiary/<string:beneficiary_id>')
class BeneficiaryUpdate(Resource):
    @users_ns.doc('update_beneficiary', security='Bearer')
    @users_ns.expect(beneficiary_create_model)
    @users_ns.marshal_with(success_model, code=200)
    @users_ns.response(400, 'Invalid data or validation error', error_model)
    @users_ns.response(401, 'Unauthorized', error_model)
    @users_ns.response(404, 'Beneficiary not found', error_model)
    @users_ns.response(500, 'Internal server error', error_model)
    def put(self, beneficiary_id):
        """
        Update beneficiary
        
        Update beneficiary information. All fields are optional for partial updates.
        """
        pass  # Implementation handled by actual users.py route

@users_ns.route('/user/<string:id>/beneficiary/<string:beneficiary_id>')
class BeneficiaryDelete(Resource):
    @users_ns.doc('delete_beneficiary', security='Bearer')
    @users_ns.marshal_with(success_model, code=200)
    @users_ns.response(401, 'Unauthorized', error_model)
    @users_ns.response(404, 'Beneficiary not found', error_model)
    @users_ns.response(500, 'Internal server error', error_model)
    def delete(self, id, beneficiary_id):
        """
        Delete beneficiary
        
        Remove a beneficiary from the user's account.
        """
        pass  # Implementation handled by actual users.py route
