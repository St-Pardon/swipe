from flask_restx import Resource, fields
from flask import request
from app.swagger import api
from app.api_docs import success_model, error_model, success_with_pagination, pagination_model

# Create namespace for invoices
invoices_ns = api.namespace('invoices', description='Invoice management operations')

# Invoice Models
invoice_model = api.model('Invoice', {
    'id': fields.String(description='Invoice ID'),
    'title': fields.String(description='Invoice title', example='Web Development Services'),
    'description': fields.String(description='Invoice description', example='Frontend and backend development for e-commerce platform'),
    'client_name': fields.String(description='Client name', example='ABC Corporation'),
    'client_email': fields.String(description='Client email', example='billing@abccorp.com'),
    'amount': fields.Float(description='Invoice amount', example=2500.00),
    'currency': fields.String(description='Currency code', example='USD'),
    'tax_amount': fields.Float(description='Tax amount', example=250.00),
    'discount_amount': fields.Float(description='Discount amount', example=0.00),
    'total_amount': fields.Float(description='Total amount including tax and discount', example=2750.00),
    'due_date': fields.String(description='Due date', example='2024-01-15'),
    'status': fields.String(description='Invoice status', enum=['draft', 'pending', 'paid', 'overdue', 'cancelled'], example='draft'),
    'notes': fields.String(description='Additional notes', example='Payment due within 30 days'),
    'created_at': fields.String(description='Creation timestamp'),
    'updated_at': fields.String(description='Last update timestamp')
})

invoice_create_model = api.model('InvoiceCreate', {
    'title': fields.String(required=True, description='Invoice title', example='Web Development Services'),
    'description': fields.String(description='Invoice description', example='Frontend and backend development for e-commerce platform'),
    'client_name': fields.String(required=True, description='Client name', example='ABC Corporation'),
    'client_email': fields.String(required=True, description='Client email', example='billing@abccorp.com'),
    'amount': fields.Float(required=True, description='Invoice amount', example=2500.00),
    'currency': fields.String(description='Currency code', example='USD'),
    'tax_amount': fields.Float(description='Tax amount', example=250.00),
    'discount_amount': fields.Float(description='Discount amount', example=0.00),
    'due_date': fields.String(description='Due date (YYYY-MM-DD format)', example='2024-01-15'),
    'notes': fields.String(description='Additional notes', example='Payment due within 30 days'),
    'status': fields.String(description='Initial invoice status', enum=['draft', 'pending'], example='draft')
})

invoice_update_model = api.model('InvoiceUpdate', {
    'title': fields.String(description='Invoice title', example='Updated Web Development Services'),
    'description': fields.String(description='Invoice description', example='Updated frontend and backend development for e-commerce platform'),
    'client_name': fields.String(description='Client name', example='ABC Corporation'),
    'client_email': fields.String(description='Client email', example='billing@abccorp.com'),
    'amount': fields.Float(description='Invoice amount', example=3000.00),
    'currency': fields.String(description='Currency code', example='USD'),
    'tax_amount': fields.Float(description='Tax amount', example=300.00),
    'discount_amount': fields.Float(description='Discount amount', example=0.00),
    'due_date': fields.String(description='Due date (YYYY-MM-DD format)', example='2024-01-20'),
    'notes': fields.String(description='Additional notes', example='Updated payment terms'),
    'status': fields.String(description='Invoice status', enum=['draft', 'pending', 'paid', 'overdue', 'cancelled'], example='pending')
})

@invoices_ns.route('')
class InvoiceList(Resource):
    @invoices_ns.doc('get_invoices', security='Bearer')
    @invoices_ns.param('page', 'Page number (default: 1)', type='int', required=False)
    @invoices_ns.param('size', 'Items per page (default: 10)', type='int', required=False)
    @invoices_ns.param('search', 'Search term for filtering invoices', required=False)
    @invoices_ns.param('status', 'Filter by invoice status (draft, pending, paid, overdue, cancelled)', required=False)
    @invoices_ns.param('sort_by', 'Field to sort by (created_at, due_date, amount)', required=False)
    @invoices_ns.param('sort_order', 'Sort order (asc, desc)', required=False)
    @invoices_ns.marshal_with(success_with_pagination, code=200)
    @invoices_ns.response(401, 'Unauthorized', error_model)
    @invoices_ns.response(500, 'Internal server error', error_model)
    def get(self):
        """
        Get all invoices with filtering and pagination
        
        Retrieve a paginated list of all invoices belonging to the authenticated user.
        Supports filtering by status, search functionality, and sorting.
        """
        pass  # Implementation handled by actual invoice.py route

    @invoices_ns.doc('create_invoice', security='Bearer')
    @invoices_ns.expect(invoice_create_model)
    @invoices_ns.marshal_with(success_model, code=201)
    @invoices_ns.response(400, 'Invalid data or validation error', error_model)
    @invoices_ns.response(401, 'Unauthorized', error_model)
    @invoices_ns.response(500, 'Internal server error', error_model)
    def post(self):
        """
        Create a new invoice
        
        Create a new invoice with client details, amount, and payment terms.
        The invoice can be created in draft or pending status.
        """
        pass  # Implementation handled by actual invoice.py route

@invoices_ns.route('/draft')
class DraftInvoices(Resource):
    @invoices_ns.doc('get_draft_invoices', security='Bearer')
    @invoices_ns.param('page', 'Page number (default: 1)', type='int', required=False)
    @invoices_ns.param('size', 'Items per page (default: 10)', type='int', required=False)
    @invoices_ns.marshal_with(success_with_pagination, code=200)
    @invoices_ns.response(401, 'Unauthorized', error_model)
    @invoices_ns.response(500, 'Internal server error', error_model)
    def get(self):
        """
        Get draft invoices
        
        Retrieve a paginated list of invoices with draft status.
        These are invoices that have been created but not yet sent to clients.
        """
        pass  # Implementation handled by actual invoice.py route

@invoices_ns.route('/pending')
class PendingInvoices(Resource):
    @invoices_ns.doc('get_pending_invoices', security='Bearer')
    @invoices_ns.param('page', 'Page number (default: 1)', type='int', required=False)
    @invoices_ns.param('size', 'Items per page (default: 10)', type='int', required=False)
    @invoices_ns.marshal_with(success_with_pagination, code=200)
    @invoices_ns.response(401, 'Unauthorized', error_model)
    @invoices_ns.response(500, 'Internal server error', error_model)
    def get(self):
        """
        Get pending invoices
        
        Retrieve a paginated list of invoices with pending status.
        These are invoices that have been sent to clients but not yet paid.
        """
        pass  # Implementation handled by actual invoice.py route

@invoices_ns.route('/due')
class DueInvoices(Resource):
    @invoices_ns.doc('get_due_invoices', security='Bearer')
    @invoices_ns.param('page', 'Page number (default: 1)', type='int', required=False)
    @invoices_ns.param('size', 'Items per page (default: 10)', type='int', required=False)
    @invoices_ns.marshal_with(success_with_pagination, code=200)
    @invoices_ns.response(401, 'Unauthorized', error_model)
    @invoices_ns.response(500, 'Internal server error', error_model)
    def get(self):
        """
        Get due invoices
        
        Retrieve a paginated list of invoices that are due for payment.
        Includes pending invoices that have reached or passed their due date.
        """
        pass  # Implementation handled by actual invoice.py route

@invoices_ns.route('/overdue')
class OverdueInvoices(Resource):
    @invoices_ns.doc('get_overdue_invoices', security='Bearer')
    @invoices_ns.param('page', 'Page number (default: 1)', type='int', required=False)
    @invoices_ns.param('size', 'Items per page (default: 10)', type='int', required=False)
    @invoices_ns.marshal_with(success_with_pagination, code=200)
    @invoices_ns.response(401, 'Unauthorized', error_model)
    @invoices_ns.response(500, 'Internal server error', error_model)
    def get(self):
        """
        Get overdue invoices
        
        Retrieve a paginated list of invoices that are past their due date.
        These invoices have not been paid and are considered overdue.
        """
        pass  # Implementation handled by actual invoice.py route

@invoices_ns.route('/<string:invoice_id>')
class InvoiceDetail(Resource):
    @invoices_ns.doc('get_invoice', security='Bearer')
    @invoices_ns.marshal_with(success_model, code=200)
    @invoices_ns.response(401, 'Unauthorized', error_model)
    @invoices_ns.response(404, 'Invoice not found', error_model)
    @invoices_ns.response(500, 'Internal server error', error_model)
    def get(self, invoice_id):
        """
        Get specific invoice
        
        Retrieve detailed information about a specific invoice by ID.
        Includes all invoice details and current status.
        """
        pass  # Implementation handled by actual invoice.py route

    @invoices_ns.doc('update_invoice', security='Bearer')
    @invoices_ns.expect(invoice_update_model)
    @invoices_ns.marshal_with(success_model, code=200)
    @invoices_ns.response(400, 'Invalid data or validation error', error_model)
    @invoices_ns.response(401, 'Unauthorized', error_model)
    @invoices_ns.response(404, 'Invoice not found', error_model)
    @invoices_ns.response(500, 'Internal server error', error_model)
    def put(self, invoice_id):
        """
        Update invoice
        
        Update an existing invoice with new information.
        Can update invoice details, amounts, and status.
        """
        pass  # Implementation handled by actual invoice.py route

    @invoices_ns.doc('delete_invoice', security='Bearer')
    @invoices_ns.marshal_with(success_model, code=200)
    @invoices_ns.response(401, 'Unauthorized', error_model)
    @invoices_ns.response(404, 'Invoice not found', error_model)
    @invoices_ns.response(500, 'Internal server error', error_model)
    def delete(self, invoice_id):
        """
        Delete invoice
        
        Delete an invoice permanently. This action cannot be undone.
        Only invoices in draft status can be deleted.
        """
        pass  # Implementation handled by actual invoice.py route
