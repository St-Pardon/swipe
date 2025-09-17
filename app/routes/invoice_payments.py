from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.invoice_model import Invoice
from app.models.user_model import User
from app.services.payment_service import PaymentService
from app.config.payment_config import PaymentConfig
from app.extensions import db
from decimal import Decimal
import logging
from app.routes.transaction import create_transaction

invoice_payments_bp = Blueprint('invoice_payments', __name__)
logger = logging.getLogger(__name__)

@invoice_payments_bp.route("/invoices/<string:invoice_id>/pay", methods=["POST"])
def create_invoice_payment_session(invoice_id):
    """
    Create a Stripe checkout session for invoice payment
    """
    try:
        data = request.get_json() or {}
        
        # Get invoice
        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            return jsonify({
                "status": 404,
                "message": "Invoice not found"
            }), 404
        
        # Check if invoice is already paid
        if hasattr(invoice, 'status') and invoice.status == 'paid':
            return jsonify({
                "status": 400,
                "message": "Invoice is already paid"
            }), 400
        
        # Get invoice amount and currency
        amount = Decimal(str(invoice.amount))
        currency = getattr(invoice, 'currency', 'USD')
        
        # Get success and cancel URLs from request or use defaults
        success_url = data.get('success_url')
        cancel_url = data.get('cancel_url')
        
        # Create checkout session using PaymentService
        payment_intent, checkout_url = PaymentService.create_checkout_session(
            user_id=invoice.user_id,
            invoice_id=invoice_id,
            amount=amount,
            currency=currency,
            success_url=success_url,
            cancel_url=cancel_url
        )
        # Log transaction as pending invoice payment intent
        try:
            create_transaction(
                user_id=invoice.user_id,
                txn_type="invoice_payment_intent",
                status="pending",
                amount=amount,
                currency_code=currency,
                description=f"Invoice {invoice_id} payment intent",
                metadata={
                    "payment_intent_id": str(payment_intent.id),
                    "invoice_id": invoice_id,
                },
            )
            db.session.commit()
        except Exception:
            db.session.rollback()
            # Non-blocking if logging fails
        
        # Update invoice with payment session info
        if hasattr(invoice, 'payment_session_id'):
            invoice.payment_session_id = payment_intent.client_secret
        if hasattr(invoice, 'payment_link'):
            invoice.payment_link = checkout_url
        if hasattr(invoice, 'payment_status'):
            invoice.payment_status = 'pending'
        
        db.session.commit()
        
        return jsonify({
            "status": 201,
            "message": "Payment session created successfully",
            "data": {
                "payment_url": checkout_url,
                "payment_intent_id": payment_intent.id,
                "amount": str(amount),
                "currency": currency,
                "invoice_id": invoice_id
            }
        }), 201
        
    except ValueError as e:
        return jsonify({
            "status": 400,
            "message": str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error creating invoice payment session: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "An error occurred while creating payment session"
        }), 500

@invoice_payments_bp.route("/invoices/<string:invoice_id>/payment-success", methods=["GET"])
def handle_invoice_payment_success(invoice_id):
    """
    Handle successful invoice payment redirect
    """
    try:
        session_id = request.args.get('session_id')
        
        if not session_id:
            return jsonify({
                "status": 400,
                "message": "Missing session_id parameter"
            }), 400
        
        # Get invoice
        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            return jsonify({
                "status": 404,
                "message": "Invoice not found"
            }), 404
        
        # Find payment intent by session ID
        from app.models.payment_intent_model import PaymentIntent
        payment_intent = PaymentIntent.query.filter_by(
            invoice_id=invoice_id,
            client_secret=session_id
        ).first()
        
        if not payment_intent:
            return jsonify({
                "status": 404,
                "message": "Payment session not found"
            }), 404
        
        # Check payment status
        payment_status = payment_intent.status
        
        return jsonify({
            "status": 200,
            "message": "Payment status retrieved successfully",
            "data": {
                "invoice_id": invoice_id,
                "payment_status": payment_status,
                "payment_intent_id": payment_intent.id,
                "amount": str(payment_intent.amount),
                "currency": payment_intent.currency,
                "is_successful": payment_intent.is_successful()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error handling payment success: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "An error occurred while processing payment success"
        }), 500

@invoice_payments_bp.route("/invoices/<string:invoice_id>/payment-cancel", methods=["GET"])
def handle_invoice_payment_cancel(invoice_id):
    """
    Handle canceled invoice payment redirect
    """
    try:
        # Get invoice
        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            return jsonify({
                "status": 404,
                "message": "Invoice not found"
            }), 404
        
        return jsonify({
            "status": 200,
            "message": "Payment was canceled",
            "data": {
                "invoice_id": invoice_id,
                "payment_status": "canceled",
                "message": "Payment was canceled by the user"
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error handling payment cancel: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "An error occurred while processing payment cancellation"
        }), 500

@invoice_payments_bp.route("/invoices/<string:invoice_id>/payment-status", methods=["GET"])
@jwt_required()
def get_invoice_payment_status(invoice_id):
    """
    Get current payment status for an invoice
    """
    try:
        user_id = get_jwt_identity()
        
        # Get invoice and verify ownership
        invoice = Invoice.query.filter_by(id=invoice_id, user_id=user_id).first()
        if not invoice:
            return jsonify({
                "status": 404,
                "message": "Invoice not found"
            }), 404
        
        # Get latest payment intent for this invoice
        from app.models.payment_intent_model import PaymentIntent
        payment_intent = PaymentIntent.query.filter_by(
            invoice_id=invoice_id
        ).order_by(PaymentIntent.created_at.desc()).first()
        
        response_data = {
            "invoice_id": invoice_id,
            "invoice_amount": str(invoice.amount),
            "invoice_currency": getattr(invoice, 'currency', 'USD'),
            "payment_status": getattr(invoice, 'payment_status', 'unpaid')
        }
        
        if payment_intent:
            response_data.update({
                "payment_intent_id": payment_intent.id,
                "payment_intent_status": payment_intent.status,
                "payment_amount": str(payment_intent.amount),
                "payment_currency": payment_intent.currency,
                "is_successful": payment_intent.is_successful(),
                "created_at": payment_intent.created_at.isoformat(),
                "confirmed_at": payment_intent.confirmed_at.isoformat() if payment_intent.confirmed_at else None
            })
        
        return jsonify({
            "status": 200,
            "message": "Payment status retrieved successfully",
            "data": response_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting payment status: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "An error occurred while retrieving payment status"
        }), 500

@invoice_payments_bp.route("/invoices/<string:invoice_id>/payment-link", methods=["GET"])
@jwt_required()
def get_invoice_payment_link(invoice_id):
    """
    Get or create payment link for an invoice
    """
    try:
        user_id = get_jwt_identity()
        
        # Get invoice and verify ownership
        invoice = Invoice.query.filter_by(id=invoice_id, user_id=user_id).first()
        if not invoice:
            return jsonify({
                "status": 404,
                "message": "Invoice not found"
            }), 404
        
        # Check if invoice already has a payment link
        existing_link = getattr(invoice, 'payment_link', None)
        if existing_link:
            return jsonify({
                "status": 200,
                "message": "Payment link retrieved successfully",
                "data": {
                    "invoice_id": invoice_id,
                    "payment_link": existing_link,
                    "amount": str(invoice.amount),
                    "currency": getattr(invoice, 'currency', 'USD')
                }
            }), 200
        
        # Create new payment session
        amount = Decimal(str(invoice.amount))
        currency = getattr(invoice, 'currency', 'USD')
        
        payment_intent, checkout_url = PaymentService.create_checkout_session(
            user_id=user_id,
            invoice_id=invoice_id,
            amount=amount,
            currency=currency
        )
        # Log transaction for the new payment intent
        try:
            create_transaction(
                user_id=user_id,
                txn_type="invoice_payment_intent",
                status="pending",
                amount=amount,
                currency_code=currency,
                description=f"Invoice {invoice_id} payment intent",
                metadata={
                    "payment_intent_id": str(payment_intent.id),
                    "invoice_id": invoice_id,
                },
            )
            db.session.commit()
        except Exception:
            db.session.rollback()
            # Non-blocking if logging fails
        
        # Update invoice with payment link
        if hasattr(invoice, 'payment_link'):
            invoice.payment_link = checkout_url
        if hasattr(invoice, 'payment_session_id'):
            invoice.payment_session_id = payment_intent.client_secret
        if hasattr(invoice, 'payment_status'):
            invoice.payment_status = 'pending'
        
        db.session.commit()
        
        return jsonify({
            "status": 201,
            "message": "Payment link created successfully",
            "data": {
                "invoice_id": invoice_id,
                "payment_link": checkout_url,
                "payment_intent_id": payment_intent.id,
                "amount": str(amount),
                "currency": currency
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating payment link: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "An error occurred while creating payment link"
        }), 500
