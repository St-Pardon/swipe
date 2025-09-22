from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from sqlalchemy import or_, and_, desc, asc
from datetime import datetime

from app.extensions import db
from app.models.invoice_model import Invoice, InvoiceStatus
from app.schema.invoice_schema import (
    InvoiceCreateSchema, 
    InvoiceUpdateSchema, 
    InvoiceResponseSchema, 
    InvoiceFilterSchema
)
import logging

invoice_bp = Blueprint('invoice', __name__)
logger = logging.getLogger(__name__)

@invoice_bp.route("/invoices", methods=["POST"])
@jwt_required()
def create_invoice():
    """Create a new invoice"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate input data
        schema = InvoiceCreateSchema()
        validated_data = schema.load(data)
        
        # Create invoice
        status = validated_data.pop('status', 'draft')
        invoice = Invoice.create_invoice(user_id=user_id, **validated_data)
        invoice.set_status_from_string(status)
        db.session.add(invoice)
        db.session.commit()
        
        # Return created invoice
        response_schema = InvoiceResponseSchema()
        result = response_schema.dump(invoice)
        
        return jsonify({
            "status": 201,
            "message": "Invoice created successfully",
            "data": result
        }), 201
        
    except ValidationError as e:
        return jsonify({
            "status": 400,
            "message": "Validation error",
            "errors": e.messages
        }), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating invoice: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "An error occurred while creating the invoice",
            "error": str(e)
        }), 500

@invoice_bp.route("/invoices", methods=["GET"])
@jwt_required()
def get_invoices():
    """Get all invoices with filtering, search, and pagination"""
    try:
        user_id = get_jwt_identity()
        
        # Validate query parameters
        filter_schema = InvoiceFilterSchema()
        filters = filter_schema.load(request.args.to_dict())
        
        # Base query
        query = Invoice.query.filter_by(user_id=user_id)
        
        # Apply search
        if filters.get('search'):
            search_term = f"%{filters['search']}%"
            query = query.filter(or_(
                Invoice.title.ilike(search_term),
                Invoice.description.ilike(search_term),
                Invoice.invoice_number.ilike(search_term),
                Invoice.client_name.ilike(search_term),
                Invoice.client_email.ilike(search_term),
                Invoice.notes.ilike(search_term)
            ))
        
        # Apply status filter
        if filters.get('status'):
            status_mapping = {
                'draft': InvoiceStatus.DRAFT,
                'pending': InvoiceStatus.PENDING,
                'paid': InvoiceStatus.PAID,
                'overdue': InvoiceStatus.OVERDUE,
                'cancelled': InvoiceStatus.CANCELLED
            }
            status_enum = status_mapping.get(filters['status'].lower())
            if status_enum:
                query = query.filter(Invoice.status == status_enum)
        
        # Apply client filters
        if filters.get('client_name'):
            query = query.filter(Invoice.client_name.ilike(f"%{filters['client_name']}%"))
        
        if filters.get('client_email'):
            query = query.filter(Invoice.client_email.ilike(f"%{filters['client_email']}%"))
        
        # Apply currency filter
        if filters.get('currency'):
            query = query.filter(Invoice.currency == filters['currency'])
        
        # Apply date filters
        if filters.get('issue_date_from'):
            query = query.filter(Invoice.issue_date >= filters['issue_date_from'])
        
        if filters.get('issue_date_to'):
            query = query.filter(Invoice.issue_date <= filters['issue_date_to'])
        
        if filters.get('due_date_from'):
            query = query.filter(Invoice.due_date >= filters['due_date_from'])
        
        if filters.get('due_date_to'):
            query = query.filter(Invoice.due_date <= filters['due_date_to'])
        
        # Apply amount filters
        if filters.get('amount_min'):
            query = query.filter(Invoice.total_amount >= filters['amount_min'])
        
        if filters.get('amount_max'):
            query = query.filter(Invoice.total_amount <= filters['amount_max'])
        
        # Apply special filters
        if filters.get('overdue_only'):
            query = query.filter(and_(
                Invoice.due_date < datetime.utcnow(),
                Invoice.status.notin_([InvoiceStatus.PAID, InvoiceStatus.CANCELLED])
            ))
        
        if filters.get('due_soon_only'):
            from datetime import timedelta
            seven_days_from_now = datetime.utcnow() + timedelta(days=7)
            query = query.filter(and_(
                Invoice.due_date <= seven_days_from_now,
                Invoice.due_date >= datetime.utcnow(),
                Invoice.status.notin_([InvoiceStatus.PAID, InvoiceStatus.CANCELLED])
            ))
        
        if filters.get('unpaid_only'):
            query = query.filter(Invoice.status.notin_([InvoiceStatus.PAID]))
        
        # Apply sorting
        sort_field = getattr(Invoice, filters.get('sort_by', 'created_at'))
        if filters.get('sort_order') == 'asc':
            query = query.order_by(asc(sort_field))
        else:
            query = query.order_by(desc(sort_field))
        
        # Apply pagination
        page = filters.get('page', 1)
        size = filters.get('size', 10)
        invoices = query.paginate(page=page, per_page=size, error_out=False)
        
        # Serialize results
        response_schema = InvoiceResponseSchema(many=True)
        result = response_schema.dump(invoices.items)
        
        return jsonify({
            "status": 200,
            "message": "Invoices retrieved successfully",
            "data": result,
            "pagination": {
                "page": page,
                "size": size,
                "total": invoices.total,
                "pages": invoices.pages,
                "has_next": invoices.has_next,
                "has_prev": invoices.has_prev
            }
        }), 200
        
    except ValidationError as e:
        return jsonify({
            "status": 400,
            "message": "Invalid filter parameters",
            "errors": e.messages
        }), 400
    except Exception as e:
        logger.error(f"Error retrieving invoices: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "An error occurred while retrieving invoices",
            "error": str(e)
        }), 500

@invoice_bp.route("/invoices/draft", methods=["GET"])
@jwt_required()
def get_draft_invoices():
    """Get all draft invoices"""
    try:
        user_id = get_jwt_identity()
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)
        
        # Query draft invoices
        invoices = Invoice.query.filter_by(
            user_id=user_id, 
            status=InvoiceStatus.DRAFT
        ).order_by(desc(Invoice.created_at)).paginate(
            page=page, per_page=size, error_out=False
        )
        
        # Serialize results
        response_schema = InvoiceResponseSchema(many=True)
        result = response_schema.dump(invoices.items)
        
        return jsonify({
            "status": 200,
            "message": "Draft invoices retrieved successfully",
            "data": result,
            "pagination": {
                "page": page,
                "size": size,
                "total": invoices.total,
                "pages": invoices.pages
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving draft invoices: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "An error occurred while retrieving draft invoices",
            "error": str(e)
        }), 500

@invoice_bp.route("/invoices/pending", methods=["GET"])
@jwt_required()
def get_pending_invoices():
    """Get all pending invoices"""
    try:
        user_id = get_jwt_identity()
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)
        
        # Query pending invoices
        invoices = Invoice.query.filter_by(
            user_id=user_id, 
            status=InvoiceStatus.PENDING
        ).order_by(desc(Invoice.due_date)).paginate(
            page=page, per_page=size, error_out=False
        )
        
        # Serialize results
        response_schema = InvoiceResponseSchema(many=True)
        result = response_schema.dump(invoices.items)
        
        return jsonify({
            "status": 200,
            "message": "Pending invoices retrieved successfully",
            "data": result,
            "pagination": {
                "page": page,
                "size": size,
                "total": invoices.total,
                "pages": invoices.pages
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving pending invoices: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "An error occurred while retrieving pending invoices",
            "error": str(e)
        }), 500

@invoice_bp.route("/invoices/due", methods=["GET"])
@jwt_required()
def get_due_invoices():
    """Get all invoices due within 7 days"""
    try:
        user_id = get_jwt_identity()
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)
        
        # Calculate date range
        from datetime import timedelta
        now = datetime.utcnow()
        seven_days_from_now = now + timedelta(days=7)
        
        # Query due invoices
        invoices = Invoice.query.filter(and_(
            Invoice.user_id == user_id,
            Invoice.due_date <= seven_days_from_now,
            Invoice.due_date >= now,
            Invoice.status.notin_([InvoiceStatus.PAID, InvoiceStatus.CANCELLED])
        )).order_by(asc(Invoice.due_date)).paginate(
            page=page, per_page=size, error_out=False
        )
        
        # Serialize results
        response_schema = InvoiceResponseSchema(many=True)
        result = response_schema.dump(invoices.items)
        
        return jsonify({
            "status": 200,
            "message": "Due invoices retrieved successfully",
            "data": result,
            "pagination": {
                "page": page,
                "size": size,
                "total": invoices.total,
                "pages": invoices.pages
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving due invoices: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "An error occurred while retrieving due invoices",
            "error": str(e)
        }), 500

@invoice_bp.route("/invoices/overdue", methods=["GET"])
@jwt_required()
def get_overdue_invoices():
    """Get all overdue invoices"""
    try:
        user_id = get_jwt_identity()
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)
        
        # Query overdue invoices
        invoices = Invoice.query.filter(and_(
            Invoice.user_id == user_id,
            Invoice.due_date < datetime.utcnow(),
            Invoice.status.notin_([InvoiceStatus.PAID, InvoiceStatus.CANCELLED])
        )).order_by(desc(Invoice.due_date)).paginate(
            page=page, per_page=size, error_out=False
        )
        
        # Serialize results
        response_schema = InvoiceResponseSchema(many=True)
        result = response_schema.dump(invoices.items)
        
        return jsonify({
            "status": 200,
            "message": "Overdue invoices retrieved successfully",
            "data": result,
            "pagination": {
                "page": page,
                "size": size,
                "total": invoices.total,
                "pages": invoices.pages
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving overdue invoices: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "An error occurred while retrieving overdue invoices",
            "error": str(e)
        }), 500

@invoice_bp.route("/invoices/<string:invoice_id>", methods=["GET"])
@jwt_required()
def get_invoice(invoice_id):
    """Get a specific invoice by ID"""
    try:
        user_id = get_jwt_identity()
        
        # Find invoice
        invoice = Invoice.query.filter_by(id=invoice_id, user_id=user_id).first()
        if not invoice:
            return jsonify({
                "status": 404,
                "message": "Invoice not found"
            }), 404
        
        # Update status if needed
        invoice.update_status()
        db.session.commit()
        
        # Serialize result
        response_schema = InvoiceResponseSchema()
        result = response_schema.dump(invoice)
        
        return jsonify({
            "status": 200,
            "message": "Invoice retrieved successfully",
            "data": result
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving invoice: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "An error occurred while retrieving the invoice",
            "error": str(e)
        }), 500

@invoice_bp.route("/invoices/<string:invoice_id>", methods=["PUT"])
@jwt_required()
def update_invoice(invoice_id):
    """Update an existing invoice"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Find invoice
        invoice = Invoice.query.filter_by(id=invoice_id, user_id=user_id).first()
        if not invoice:
            return jsonify({
                "status": 404,
                "message": "Invoice not found"
            }), 404
        
        # Validate input data
        schema = InvoiceUpdateSchema()
        validated_data = schema.load(data)
        
        # Update invoice fields
        for field, value in validated_data.items():
            setattr(invoice, field, value)
        
        # Recalculate total if financial fields changed
        if any(field in validated_data for field in ['amount', 'tax_amount', 'discount_amount']):
            invoice.calculate_total()
        
        # Update status if needed
        invoice.update_status()
        
        db.session.commit()
        
        # Return updated invoice
        response_schema = InvoiceResponseSchema()
        result = response_schema.dump(invoice)
        
        return jsonify({
            "status": 200,
            "message": "Invoice updated successfully",
            "data": result
        }), 200
        
    except ValidationError as e:
        return jsonify({
            "status": 400,
            "message": "Validation error",
            "errors": e.messages
        }), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating invoice: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "An error occurred while updating the invoice",
            "error": str(e)
        }), 500

@invoice_bp.route("/invoices/<string:invoice_id>", methods=["DELETE"])
@jwt_required()
def delete_invoice(invoice_id):
    """Delete an invoice"""
    try:
        user_id = get_jwt_identity()
        
        # Find invoice
        invoice = Invoice.query.filter_by(id=invoice_id, user_id=user_id).first()
        if not invoice:
            return jsonify({
                "status": 404,
                "message": "Invoice not found"
            }), 404
        
        # Check if invoice can be deleted (e.g., not paid)
        if invoice.status == InvoiceStatus.PAID:
            return jsonify({
                "status": 400,
                "message": "Cannot delete a paid invoice"
            }), 400
        
        # Delete invoice
        db.session.delete(invoice)
        db.session.commit()
        
        return jsonify({
            "status": 200,
            "message": "Invoice deleted successfully"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting invoice: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "An error occurred while deleting the invoice",
            "error": str(e)
        }), 500
