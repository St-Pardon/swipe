from flask_restx import Resource
from flask import request
from app.swagger import wallets_ns
from app.api_docs import transfer_model, transfer_response, withdrawal_model, success_model, error_model

@wallets_ns.route('/wallets/transfer')
class WalletTransfer(Resource):
    @wallets_ns.doc('wallet_transfer')
    @wallets_ns.expect(transfer_model)
    @wallets_ns.marshal_with(transfer_response, code=201)
    @wallets_ns.response(400, 'Invalid transfer data', error_model)
    @wallets_ns.response(401, 'Unauthorized', error_model)
    @wallets_ns.response(404, 'Account or beneficiary not found', error_model)
    @wallets_ns.response(422, 'Validation error', error_model)
    def post(self):
        """
        Create a transfer
        
        Transfer funds between accounts, to beneficiaries, customers, or external accounts.
        
        Transfer Types:
        - **beneficiary**: Transfer to a saved beneficiary
        - **internal**: Transfer between user's own accounts
        - **customer**: Transfer to another Swipe customer by email
        - **external**: Transfer to external bank account (non-customer)
        """
        pass  # Implementation handled by actual wallet.py route

@wallets_ns.route('/wallets/withdraw')
class WalletWithdraw(Resource):
    @wallets_ns.doc('wallet_withdraw')
    @wallets_ns.expect(withdrawal_model)
    @wallets_ns.marshal_with(success_model, code=201)
    @wallets_ns.response(400, 'Invalid withdrawal data', error_model)
    @wallets_ns.response(401, 'Unauthorized', error_model)
    @wallets_ns.response(404, 'Account not found', error_model)
    @wallets_ns.response(422, 'Validation error', error_model)
    def post(self):
        """
        Withdraw funds
        
        Withdraw funds from wallet to external bank account by account number.
        The account number must belong to the authenticated user.
        """
        pass  # Implementation handled by actual wallet.py route
