from flask_restx import Resource
from flask import request
from app.swagger import accounts_ns
from app.api_docs import account_model, success_model, error_model

@accounts_ns.route('/accounts')
class AccountsList(Resource):
    @accounts_ns.doc('get_accounts')
    @accounts_ns.marshal_list_with(account_model, code=200)
    @accounts_ns.response(401, 'Unauthorized', error_model)
    def get(self):
        """
        Get user accounts
        
        Retrieve all accounts belonging to the authenticated user.
        """
        pass  # Implementation handled by actual account.py route

    @accounts_ns.doc('create_account')
    @accounts_ns.expect(account_model)
    @accounts_ns.marshal_with(success_model, code=201)
    @accounts_ns.response(400, 'Invalid account data', error_model)
    @accounts_ns.response(401, 'Unauthorized', error_model)
    @accounts_ns.response(422, 'Validation error', error_model)
    def post(self):
        """
        Create new account
        
        Create a new bank account for the authenticated user.
        """
        pass  # Implementation handled by actual account.py route

@accounts_ns.route('/accounts/<string:account_id>')
class AccountDetail(Resource):
    @accounts_ns.doc('get_account')
    @accounts_ns.marshal_with(account_model, code=200)
    @accounts_ns.response(401, 'Unauthorized', error_model)
    @accounts_ns.response(404, 'Account not found', error_model)
    def get(self, account_id):
        """
        Get account details
        
        Retrieve details of a specific account by ID.
        """
        pass  # Implementation handled by actual account.py route
