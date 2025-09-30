from flask_restx import Resource, fields
from flask_jwt_extended import jwt_required
from app.swagger import accounts_ns
from app.api_docs import (
    account_create_model,
    success_model,
    error_model
)

# Shared models specific to this module
account_update_model = accounts_ns.clone(
    'AccountUpdate',
    account_create_model,
    {
        'is_default': fields.Boolean(description='Set as default account', example=False)
    }
)

close_account_model = accounts_ns.model('AccountClose', {
    'account_id': fields.String(required=True, description='Account ID to close')
})


@accounts_ns.route('/accounts')
class AccountsCollection(Resource):
    @accounts_ns.doc('list_accounts', security='Bearer')
    @accounts_ns.marshal_with(success_model, code=200, description='Accounts retrieved successfully')
    @accounts_ns.response(401, 'Unauthorized', error_model)
    @accounts_ns.response(500, 'Internal server error', error_model)
    @jwt_required()
    def get(self):
        """Retrieve all bank accounts belonging to the authenticated user."""
        pass  # Implemented in `app/routes/account.py`

    @accounts_ns.doc('create_account', security='Bearer')
    @accounts_ns.expect(account_create_model, validate=True)
    @accounts_ns.marshal_with(success_model, code=201, description='Account created successfully')
    @accounts_ns.response(400, 'Invalid account data', error_model)
    @accounts_ns.response(401, 'Unauthorized', error_model)
    @accounts_ns.response(422, 'Validation error', error_model)
    @accounts_ns.response(500, 'Internal server error', error_model)
    @jwt_required()
    def post(self):
        """Create a new bank account for the authenticated user."""
        pass


@accounts_ns.route('/accounts/<string:account_id>')
class AccountResource(Resource):
    @accounts_ns.doc('get_account', security='Bearer')
    @accounts_ns.marshal_with(success_model, code=200, description='Account retrieved successfully')
    @accounts_ns.response(401, 'Unauthorized', error_model)
    @accounts_ns.response(404, 'Account not found', error_model)
    @accounts_ns.response(500, 'Internal server error', error_model)
    @jwt_required()
    def get(self, account_id):
        """Retrieve details for a specific account owned by the authenticated user."""
        pass

    @accounts_ns.doc('update_account', security='Bearer')
    @accounts_ns.expect(account_update_model, validate=False)
    @accounts_ns.marshal_with(success_model, code=200, description='Account updated successfully')
    @accounts_ns.response(400, 'Invalid account data', error_model)
    @accounts_ns.response(401, 'Unauthorized', error_model)
    @accounts_ns.response(404, 'Account not found', error_model)
    @accounts_ns.response(500, 'Internal server error', error_model)
    @jwt_required()
    def put(self, account_id):
        """Update properties of an existing account owned by the authenticated user."""
        pass


@accounts_ns.route('/balances')
class AccountBalances(Resource):
    @accounts_ns.doc('get_balances', security='Bearer')
    @accounts_ns.marshal_with(success_model, code=200, description='Balances retrieved successfully')
    @accounts_ns.response(401, 'Unauthorized', error_model)
    @accounts_ns.response(500, 'Internal server error', error_model)
    @jwt_required()
    def get(self):
        """Retrieve overall balances grouped by currency for the authenticated user."""
        pass


@accounts_ns.route('/rates')
class ExchangeRates(Resource):
    @accounts_ns.doc('get_exchange_rates')
    @accounts_ns.param('base', 'Base currency code (defaults to user default or USD)')
    @accounts_ns.marshal_with(success_model, code=200, description='Exchange rates retrieved successfully')
    @accounts_ns.response(500, 'Failed to fetch exchange rates', error_model)
    def get(self):
        """Retrieve current exchange rates with applied FX margins."""
        pass


@accounts_ns.route('/wallets/balance')
class DefaultWalletBalance(Resource):
    @accounts_ns.doc('get_default_wallet_balance', security='Bearer')
    @accounts_ns.marshal_with(success_model, code=200, description='Default account balance retrieved successfully')
    @accounts_ns.response(401, 'Unauthorized', error_model)
    @accounts_ns.response(404, 'Default account not found', error_model)
    @accounts_ns.response(500, 'Internal server error', error_model)
    @jwt_required()
    def get(self):
        """Retrieve balance and currency for the authenticated user's default account."""
        pass


@accounts_ns.route('/account/close')
class AccountClose(Resource):
    @accounts_ns.doc('close_account', security='Bearer')
    @accounts_ns.expect(close_account_model, validate=True)
    @accounts_ns.marshal_with(success_model, code=200, description='Account closed successfully')
    @accounts_ns.response(401, 'Unauthorized', error_model)
    @accounts_ns.response(403, 'Admin access required', error_model)
    @accounts_ns.response(404, 'Account not found', error_model)
    @accounts_ns.response(500, 'Internal server error', error_model)
    def post(self):
        """Close a user account (admin only)."""
        pass
