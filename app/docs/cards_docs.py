from flask_restx import Resource, fields
from flask import request
from app.swagger import cards_ns, api
from app.api_docs import (virtual_card_model, virtual_card_create_model, card_fund_wallet_model,
                         success_model, error_model)

@cards_ns.route('/card')
class VirtualCardCreate(Resource):
    @cards_ns.doc('create_virtual_card', security='Bearer')
    @cards_ns.expect(virtual_card_create_model)
    @cards_ns.marshal_with(success_model, code=201)
    @cards_ns.response(400, 'Invalid data or validation error', error_model)
    @cards_ns.response(401, 'Unauthorized', error_model)
    @cards_ns.response(404, 'User or account not found', error_model)
    @cards_ns.response(500, 'Internal server error', error_model)
    def post(self):
        """
        Create virtual card
        
        Create a new virtual card linked to a user account.
        Generates card number, CVV, expiry date and creates Stripe payment method.
        """
        pass  # Implementation handled by actual card.py route

@cards_ns.route('/cards')
class VirtualCardsList(Resource):
    @cards_ns.doc('get_virtual_cards', security='Bearer')
    @cards_ns.marshal_list_with(virtual_card_model, code=200)
    @cards_ns.response(401, 'Unauthorized', error_model)
    @cards_ns.response(500, 'Internal server error', error_model)
    def get(self):
        """
        Get user's virtual cards
        
        Retrieve all virtual cards belonging to the authenticated user.
        """
        pass  # Implementation handled by actual card.py route

@cards_ns.route('/cards/<string:card_id>')
class VirtualCardDetail(Resource):
    @cards_ns.doc('get_virtual_card', security='Bearer')
    @cards_ns.marshal_with(success_model, code=200)
    @cards_ns.response(401, 'Unauthorized', error_model)
    @cards_ns.response(404, 'Card not found', error_model)
    @cards_ns.response(500, 'Internal server error', error_model)
    def get(self, card_id):
        """
        Get virtual card details
        
        Retrieve details of a specific virtual card by ID.
        """
        pass  # Implementation handled by actual card.py route

    @cards_ns.doc('update_virtual_card', security='Bearer')
    @cards_ns.expect(virtual_card_create_model)
    @cards_ns.marshal_with(success_model, code=200)
    @cards_ns.response(400, 'Invalid data or validation error', error_model)
    @cards_ns.response(401, 'Unauthorized', error_model)
    @cards_ns.response(404, 'Card not found', error_model)
    @cards_ns.response(500, 'Internal server error', error_model)
    def put(self, card_id):
        """
        Update virtual card
        
        Update virtual card information such as spending limit.
        """
        pass  # Implementation handled by actual card.py route

    @cards_ns.doc('delete_virtual_card', security='Bearer')
    @cards_ns.marshal_with(success_model, code=200)
    @cards_ns.response(401, 'Unauthorized', error_model)
    @cards_ns.response(404, 'Card not found', error_model)
    @cards_ns.response(500, 'Internal server error', error_model)
    def delete(self, card_id):
        """
        Delete virtual card
        
        Delete a virtual card and revoke associated Stripe payment method.
        """
        pass  # Implementation handled by actual card.py route

@cards_ns.route('/cards/<string:card_id>/link-payment-method')
class LinkPaymentMethod(Resource):
    @cards_ns.doc('link_payment_method', security='Bearer')
    @cards_ns.expect(api.model('LinkPaymentMethod', {
        'stripe_payment_method_id': fields.String(required=True, description='Stripe payment method ID', example='pm_1234567890abcdef')
    }))
    @cards_ns.marshal_with(success_model, code=200)
    @cards_ns.response(400, 'Invalid payment method ID', error_model)
    @cards_ns.response(401, 'Unauthorized', error_model)
    @cards_ns.response(404, 'Card not found', error_model)
    @cards_ns.response(500, 'Internal server error', error_model)
    def post(self, card_id):
        """
        Link Stripe payment method
        
        Link a Stripe payment method to a virtual card for payment processing.
        In development mode, mock payment method IDs are accepted.
        """
        pass  # Implementation handled by actual card.py route

@cards_ns.route('/cards/<string:card_id>/fund-wallet')
class CardFundWallet(Resource):
    @cards_ns.doc('fund_wallet_with_card', security='Bearer')
    @cards_ns.expect(card_fund_wallet_model)
    @cards_ns.marshal_with(success_model, code=201)
    @cards_ns.response(400, 'Invalid data or insufficient funds', error_model)
    @cards_ns.response(401, 'Unauthorized', error_model)
    @cards_ns.response(404, 'Card not found', error_model)
    @cards_ns.response(500, 'Internal server error', error_model)
    def post(self, card_id):
        """
        Fund wallet with virtual card
        
        Use virtual card to fund the associated wallet account.
        Creates payment intent and processes payment through Stripe.
        In development mode, creates mock payment and updates balance immediately.
        """
        pass  # Implementation handled by actual card_payments.py route

@cards_ns.route('/cards/<string:card_id>/transactions')
class CardTransactions(Resource):
    @cards_ns.doc('get_card_transactions', security='Bearer')
    @cards_ns.param('page', 'Page number (default: 1)', type='int', required=False)
    @cards_ns.param('per_page', 'Items per page (default: 10)', type='int', required=False)
    @cards_ns.marshal_with(success_model, code=200)
    @cards_ns.response(401, 'Unauthorized', error_model)
    @cards_ns.response(404, 'Card not found', error_model)
    @cards_ns.response(500, 'Internal server error', error_model)
    def get(self, card_id):
        """
        Get card transaction history
        
        Retrieve paginated transaction history for a specific virtual card.
        """
        pass  # Implementation handled by actual card_payments.py route

@cards_ns.route('/cards/<string:card_id>/payment-method')
class CardPaymentMethod(Resource):
    @cards_ns.doc('get_card_payment_method', security='Bearer')
    @cards_ns.marshal_with(success_model, code=200)
    @cards_ns.response(401, 'Unauthorized', error_model)
    @cards_ns.response(404, 'Card not found', error_model)
    @cards_ns.response(500, 'Internal server error', error_model)
    def get(self, card_id):
        """
        Get card payment method
        
        Retrieve the Stripe payment method linked to a virtual card.
        Returns payment method details including type, last4 digits, and expiration.
        """
        pass  # Implementation handled by actual card.py route

@cards_ns.route('/payment-methods/available')
class AvailablePaymentMethods(Resource):
    @cards_ns.doc('get_available_payment_methods', security='Bearer')
    @cards_ns.marshal_with(success_model, code=200)
    @cards_ns.response(401, 'Unauthorized', error_model)
    @cards_ns.response(500, 'Internal server error', error_model)
    def get(self):
        """
        Get available payment methods
        
        Retrieve a list of available payment methods that can be linked to virtual cards.
        In development mode, returns mock payment method data.
        In production mode, queries Stripe for available payment methods.
        """
        pass  # Implementation handled by actual card.py route

@cards_ns.route('/cards/<string:card_id>/spending-limit')
class CardSpendingLimit(Resource):
    @cards_ns.doc('update_spending_limit', security='Bearer')
    @cards_ns.expect(api.model('SpendingLimit', {
        'spending_limit': fields.Float(required=True, description='New spending limit', example=2000.00)
    }))
    @cards_ns.marshal_with(success_model, code=200)
    @cards_ns.response(400, 'Invalid spending limit', error_model)
    @cards_ns.response(401, 'Unauthorized', error_model)
    @cards_ns.response(404, 'Card not found', error_model)
    @cards_ns.response(500, 'Internal server error', error_model)
    def put(self, card_id):
        """
        Update card spending limit
        
        Update the spending limit for a virtual card.
        """
        pass  # Implementation handled by actual card_payments.py route
