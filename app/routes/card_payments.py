from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.services.payment_service import PaymentService
from app.models.payment_intent_model import PaymentIntent
from app.models.virtual_cards_model import VirtualCard
from app.models.account_model import Account
from app.schema.payment_intent_schema import PaymentIntentSchema
from app.extensions import db
from app.config.payment_config import PaymentConfig
from decimal import Decimal
import logging

card_payments_bp = Blueprint("card_payments", __name__)
logger = logging.getLogger(__name__)

@card_payments_bp.route("/cards/<string:card_id>/fund-wallet", methods=["POST"])
@jwt_required()
def fund_wallet_with_card(card_id):
    """
    Use virtual card to fund wallet account
    """
    try:
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        amount = data.get('amount')
        currency = data.get('currency', 'USD')
        description = data.get('description')
        
        if not amount:
            return jsonify({"error": "Amount is required"}), 400
        
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid amount format"}), 400
        
        if amount <= 0:
            return jsonify({"error": "Amount must be positive"}), 400
        
        # Get current user from JWT
        from flask_jwt_extended import get_jwt_identity
        user_id = get_jwt_identity()
        
        # Use PaymentService to create card payment intent
        payment_intent, client_secret = PaymentService.create_card_payment_intent(
            user_id=user_id,
            card_id=card_id,
            amount=amount,
            currency=currency,
            description=description
        )
        
        # Serialize response
        schema = PaymentIntentSchema()
        result = schema.dump(payment_intent)
        
        return jsonify({
            "message": "Wallet funding initiated successfully",
            "payment_intent": result,
            "client_secret": client_secret
        }), 201
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error funding wallet with card {card_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@card_payments_bp.route("/cards/<string:card_id>/transactions", methods=["GET"])
@jwt_required()
def get_card_transactions(card_id):
    """
    Get transaction history for a specific card
    """
    try:
        user_id = get_jwt_identity()
        
        # Verify card belongs to user
        card = VirtualCard.query.filter_by(id=card_id, user_id=user_id).first()
        
        if not card:
            return jsonify({
                "status": 404,
                "message": "Card not found"
            }), 404
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)
        
        # Get payment intents associated with this card
        from app.models.payment_intent_model import PaymentIntent
        payment_intents = PaymentIntent.query.filter_by(
            user_id=user_id,
            virtual_card_id=card_id
        ).order_by(PaymentIntent.created_at.desc()).paginate(
            page=page, per_page=size, error_out=False
        )
        
        transactions_data = []
        for intent in payment_intents.items:
            transactions_data.append({
                "transaction_id": intent.id,
                "amount": str(intent.amount),
                "currency": intent.currency,
                "status": intent.status,
                "description": intent.description,
                "created_at": intent.created_at.isoformat(),
                "confirmed_at": intent.confirmed_at.isoformat() if intent.confirmed_at else None
            })
        
        return jsonify({
            "status": 200,
            "message": "Card transactions retrieved successfully",
            "data": {
                "transactions": transactions_data,
                "pagination": {
                    "page": page,
                    "size": size,
                    "total": payment_intents.total,
                    "pages": payment_intents.pages
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving card transactions: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "An error occurred while retrieving transactions"
        }), 500

@card_payments_bp.route("/cards/<string:card_id>/spending-limit", methods=["PATCH"])
@jwt_required()
def update_spending_limit(card_id):
    """
    Update card spending limit
    """
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        if 'spending_limit' not in data:
            return jsonify({
                "status": 400,
                "message": "spending_limit is required"
            }), 400
        
        new_limit = Decimal(str(data['spending_limit']))
        
        # Verify card belongs to user
        card = VirtualCard.query.filter_by(id=card_id, user_id=user_id).first()
        
        if not card:
            return jsonify({
                "status": 404,
                "message": "Card not found"
            }), 404
        
        # Update spending limit
        card.spending_limit = float(new_limit)
        db.session.commit()
        
        return jsonify({
            "status": 200,
            "message": "Spending limit updated successfully",
            "data": {
                "card_id": card.id,
                "new_spending_limit": str(new_limit)
            }
        }), 200
        
    except ValueError as e:
        return jsonify({
            "status": 400,
            "message": f"Invalid spending limit: {str(e)}"
        }), 400
    except Exception as e:
        logger.error(f"Error updating spending limit: {str(e)}")
        db.session.rollback()
        return jsonify({
            "status": 500,
            "message": "An error occurred while updating spending limit"
        }), 500
