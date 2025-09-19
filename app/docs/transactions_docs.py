from flask_restx import Resource
from flask import request
from app.swagger import transactions_ns
from app.api_docs import transaction_model, success_with_pagination, error_model

@transactions_ns.route('/transactions')
class TransactionsList(Resource):
    @transactions_ns.doc('get_transactions', security='Bearer')
    @transactions_ns.param('page', 'Page number (default: 1)', type='int', required=False)
    @transactions_ns.param('per_page', 'Items per page (default: 10)', type='int', required=False)
    @transactions_ns.param('txn_type', 'Filter by transaction type', type='string', required=False)
    @transactions_ns.param('status', 'Filter by transaction status', type='string', required=False)
    @transactions_ns.param('start_date', 'Filter transactions from date (YYYY-MM-DD)', type='string', required=False)
    @transactions_ns.param('end_date', 'Filter transactions to date (YYYY-MM-DD)', type='string', required=False)
    @transactions_ns.marshal_with(success_with_pagination, code=200)
    @transactions_ns.response(401, 'Unauthorized', error_model)
    @transactions_ns.response(500, 'Internal server error', error_model)
    def get(self):
        """
        Get transaction history
        
        Retrieve paginated transaction history for the authenticated user.
        Supports filtering by transaction type, status, and date range.
        
        Transaction Types:
        - wallet_fund_intent: Wallet funding intent
        - wallet_fund: Completed wallet funding
        - payout: Withdrawal/payout
        - transfer: Internal/external transfer
        - card_wallet_fund_intent: Card-based wallet funding intent
        
        Transaction Status:
        - pending: Transaction initiated but not completed
        - succeeded: Transaction completed successfully
        - failed: Transaction failed
        - canceled: Transaction was canceled
        """
        pass  # Implementation handled by actual transaction.py route

@transactions_ns.route('/transactions/<string:transaction_id>')
class TransactionDetail(Resource):
    @transactions_ns.doc('get_transaction', security='Bearer')
    @transactions_ns.marshal_with(transaction_model, code=200)
    @transactions_ns.response(401, 'Unauthorized', error_model)
    @transactions_ns.response(404, 'Transaction not found', error_model)
    @transactions_ns.response(500, 'Internal server error', error_model)
    def get(self, transaction_id):
        """
        Get transaction details
        
        Retrieve details of a specific transaction by ID.
        """
        pass  # Implementation handled by actual transaction.py route
