from flask_restx import Resource, fields
from flask import request
from app.swagger import api
from app.api_docs import success_model, error_model

# Create namespace for invoice payments
invoice_payments_ns = api.namespace('invoice-payments', description='Invoice payment processing operations')

# Invoice Payment Models
invoice_payment_session_model = api.model('InvoicePaymentSession', {
    'payment_url': fields.String(description='Stripe checkout session URL', example='https://checkout.stripe.com/pay/cs_test_1234567890'),
    'payment_intent_id': fields.String(description='Stripe payment intent ID', example='pi_1234567890abcdef'),
    'session_id': fields.String(description='Stripe session ID', example='cs_test_1234567890'),
    'amount': fields.Float(description='Payment amount', example=2750.00),
    'currency': fields.String(description='Currency code', example='USD'),
    'status': fields.String(description='Payment session status', example='pending')
})

payment_session_create_model = api.model('PaymentSessionCreate', {
    'success_url': fields.String(required=True, description='URL to redirect to after successful payment', example='https://yourapp.com/payment/success'),
    'cancel_url': fields.String(required=True, description='URL to redirect to after cancelled payment', example='https://yourapp.com/payment/cancel')
})

payment_status_model = api.model('PaymentStatus', {
    'payment_intent_id': fields.String(description='Stripe payment intent ID', example='pi_1234567890abcdef'),
    'status': fields.String(description='Payment status', enum=['pending', 'succeeded', 'cancelled', 'failed'], example='pending'),
    'amount': fields.Float(description='Payment amount', example=2750.00),
    'currency': fields.String(description='Currency code', example='USD'),
    'paid_at': fields.String(description='Payment completion timestamp (if paid)', example='2024-01-15T10:30:00Z'),
    'failure_reason': fields.String(description='Reason for payment failure (if failed)', example='insufficient_funds')
})

payment_link_model = api.model('PaymentLink', {
    'payment_link': fields.String(description='Direct payment link URL', example='https://pay.stripe.com/link/test_1234567890'),
    'payment_intent_id': fields.String(description='Stripe payment intent ID', example='pi_1234567890abcdef'),
    'amount': fields.Float(description='Payment amount', example=2750.00),
    'currency': fields.String(description='Currency code', example='USD'),
    'expires_at': fields.String(description='Link expiration timestamp', example='2024-01-22T10:30:00Z')
})

@invoice_payments_ns.route('/invoices/<string:invoice_id>/pay')
class InvoicePaymentSession(Resource):
    @invoice_payments_ns.doc('create_invoice_payment_session', security='Bearer')
    @invoice_payments_ns.expect(payment_session_create_model)
    @invoice_payments_ns.marshal_with(success_model, code=201)
    @invoice_payments_ns.response(400, 'Invalid data or validation error', error_model)
    @invoice_payments_ns.response(401, 'Unauthorized', error_model)
    @invoice_payments_ns.response(404, 'Invoice not found', error_model)
    @invoice_payments_ns.response(500, 'Internal server error', error_model)
    def post(self, invoice_id):
        """
        Create invoice payment session
        
        Create a Stripe checkout session for an invoice payment.
        Returns a payment URL that redirects to Stripe's hosted checkout page.
        Supports both development mode (mock payments) and production mode (real Stripe payments).
        """
        pass  # Implementation handled by actual invoice_payments.py route

@invoice_payments_ns.route('/invoices/<string:invoice_id>/payment-status')
class InvoicePaymentStatus(Resource):
    @invoice_payments_ns.doc('get_invoice_payment_status', security='Bearer')
    @invoice_payments_ns.marshal_with(success_model, code=200)
    @invoice_payments_ns.response(401, 'Unauthorized', error_model)
    @invoice_payments_ns.response(404, 'Invoice not found', error_model)
    @invoice_payments_ns.response(500, 'Internal server error', error_model)
    def get(self, invoice_id):
        """
        Get invoice payment status
        
        Retrieve the current payment status for an invoice.
        Returns detailed information about the payment intent and its status.
        """
        pass  # Implementation handled by actual invoice_payments.py route

@invoice_payments_ns.route('/invoices/<string:invoice_id>/payment-link')
class InvoicePaymentLink(Resource):
    @invoice_payments_ns.doc('get_invoice_payment_link', security='Bearer')
    @invoice_payments_ns.marshal_with(success_model, code=200)
    @invoice_payments_ns.response(201, 'Payment link created', success_model)
    @invoice_payments_ns.response(401, 'Unauthorized', error_model)
    @invoice_payments_ns.response(404, 'Invoice not found', error_model)
    @invoice_payments_ns.response(500, 'Internal server error', error_model)
    def get(self, invoice_id):
        """
        Get or create invoice payment link
        
        Retrieve an existing payment link for an invoice or create a new one.
        Returns a direct payment link that can be shared with clients.
        The link bypasses the Stripe checkout flow for direct payment.
        """
        pass  # Implementation handled by actual invoice_payments.py route

@invoice_payments_ns.route('/invoices/<string:invoice_id>/payment-success')
class InvoicePaymentSuccess(Resource):
    @invoice_payments_ns.doc('handle_payment_success')
    @invoice_payments_ns.param('session_id', 'Stripe checkout session ID', required=True)
    @invoice_payments_ns.marshal_with(success_model, code=200)
    @invoice_payments_ns.response(400, 'Invalid session ID', error_model)
    @invoice_payments_ns.response(404, 'Invoice or session not found', error_model)
    @invoice_payments_ns.response(500, 'Internal server error', error_model)
    def get(self, invoice_id):
        """
        Handle successful payment
        
        Handle the redirect after successful payment completion.
        Updates the invoice status to 'paid' and records payment details.
        This endpoint is called by Stripe after successful payment.
        """
        pass  # Implementation handled by actual invoice_payments.py route

@invoice_payments_ns.route('/invoices/<string:invoice_id>/payment-cancel')
class InvoicePaymentCancel(Resource):
    @invoice_payments_ns.doc('handle_payment_cancel')
    @invoice_payments_ns.marshal_with(success_model, code=200)
    @invoice_payments_ns.response(404, 'Invoice not found', error_model)
    @invoice_payments_ns.response(500, 'Internal server error', error_model)
    def get(self, invoice_id):
        """
        Handle cancelled payment
        
        Handle the redirect after payment cancellation.
        Provides feedback to the user that the payment was cancelled.
        This endpoint is called by Stripe when the user cancels payment.
        """
        pass  # Implementation handled by actual invoice_payments.py route
