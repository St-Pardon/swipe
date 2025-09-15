from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.account_model import Account
from app.models.user_model import User
from app.models.payout_model import Payout
from app.services.payment_service import PaymentService
from app.config.payment_config import PaymentConfig
from app.extensions import db
from decimal import Decimal
import logging

wallet_bp = Blueprint('wallet', __name__)
logger = logging.getLogger(__name__)

@wallet_bp.route("/wallets/fund", methods=["POST"])
@jwt_required()
def fund_wallet():
    """
    Create a payment intent for wallet funding using Stripe
    """
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        # Validate required fields
        required_fields = ['amount', 'currency']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": 400,
                    "message": f"Missing required field: {field}"
                }), 400
        
        amount = Decimal(str(data['amount']))
        currency = data['currency'].upper()
        account_id = data.get('account_id')
        description = data.get('description')
        
        # If no account_id provided, use default account
        if not account_id:
            default_account = Account.query.filter_by(
                user_id=user_id, 
                is_default=True
            ).first()
            
            if not default_account:
                return jsonify({
                    "status": 404,
                    "message": "No default account found. Please specify account_id."
                }), 404
            
            account_id = default_account.id
        
        # Validate currency support
        if not PaymentConfig.is_currency_supported(currency):
            return jsonify({
                "status": 400,
                "message": f"Currency {currency} is not supported"
            }), 400
        
        # Create payment intent using PaymentService
        payment_intent, client_secret = PaymentService.create_payment_intent(
            user_id=user_id,
            account_id=account_id,
            amount=amount,
            currency=currency,
            description=description
        )
        
        return jsonify({
            "status": 201,
            "message": "Payment intent created successfully",
            "data": {
                "payment_intent_id": payment_intent.id,
                "client_secret": client_secret,
                "amount": str(payment_intent.amount),
                "currency": payment_intent.currency,
                "status": payment_intent.status
            }
        }), 201
        
    except ValueError as e:
        return jsonify({
            "status": 400,
            "message": str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error creating payment intent: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "An error occurred while processing your request"
        }), 500

@wallet_bp.route("/wallets/withdraw", methods=["POST"])
@jwt_required()
def withdraw_funds():
    """
    Create a payout for withdrawing funds to a beneficiary account
    """
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        # Validate required fields
        required_fields = ['amount', 'currency', 'beneficiary_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": 400,
                    "message": f"Missing required field: {field}"
                }), 400
        
        amount = Decimal(str(data['amount']))
        currency = data['currency'].upper()
        beneficiary_id = data['beneficiary_id']
        account_id = data.get('account_id')
        method = data.get('method', 'standard')  # standard or instant
        
        # If no account_id provided, use default account
        if not account_id:
            default_account = Account.query.filter_by(
                user_id=user_id, 
                is_default=True,
                currency_code=currency
            ).first()
            
            if not default_account:
                return jsonify({
                    "status": 404,
                    "message": f"No default {currency} account found. Please specify account_id."
                }), 404
            
            account_id = default_account.id
        
        # Validate currency support for payouts
        if not PaymentConfig.is_payout_currency_supported(currency):
            return jsonify({
                "status": 400,
                "message": f"Currency {currency} is not supported for payouts"
            }), 400
        
        # Create payout using PaymentService
        payout = PaymentService.create_payout(
            user_id=user_id,
            account_id=account_id,
            beneficiary_id=beneficiary_id,
            amount=amount,
            currency=currency,
            method=method
        )
        
        return jsonify({
            "status": 201,
            "message": "Withdrawal initiated successfully",
            "data": {
                "payout_id": payout.id,
                "gateway_payout_id": payout.gateway_payout_id,
                "amount": str(payout.amount),
                "currency": payout.currency,
                "status": payout.status,
                "method": payout.method,
                "estimated_arrival": payout.get_estimated_arrival().isoformat()
            }
        }), 201
        
    except ValueError as e:
        return jsonify({
            "status": 400,
            "message": str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error creating payout: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "An error occurred while processing your request"
        }), 500

@wallet_bp.route("/wallets/payment-intents/<string:intent_id>", methods=["GET"])
@jwt_required()
def get_payment_intent(intent_id):
    """
    Get payment intent status
    """
    try:
        user_id = get_jwt_identity()
        
        # Get payment intent from database
        from app.models.payment_intent_model import PaymentIntent
        payment_intent = PaymentIntent.query.filter_by(
            id=intent_id,
            user_id=user_id
        ).first()
        
        if not payment_intent:
            return jsonify({
                "status": 404,
                "message": "Payment intent not found"
            }), 404
        
        return jsonify({
            "status": 200,
            "message": "Payment intent retrieved successfully",
            "data": {
                "payment_intent_id": payment_intent.id,
                "gateway_intent_id": payment_intent.gateway_intent_id,
                "amount": str(payment_intent.amount),
                "currency": payment_intent.currency,
                "status": payment_intent.status,
                "intent_type": payment_intent.intent_type,
                "created_at": payment_intent.created_at.isoformat(),
                "confirmed_at": payment_intent.confirmed_at.isoformat() if payment_intent.confirmed_at else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving payment intent: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "An error occurred while retrieving payment intent"
        }), 500

@wallet_bp.route("/wallets/payouts/<string:payout_id>", methods=["GET"])
@jwt_required()
def get_payout(payout_id):
    """
    Get payout status
    """
    try:
        user_id = get_jwt_identity()
        
        # Get payout from database
        payout = Payout.query.filter_by(
            id=payout_id,
            user_id=user_id
        ).first()
        
        if not payout:
            return jsonify({
                "status": 404,
                "message": "Payout not found"
            }), 404
        
        return jsonify({
            "status": 200,
            "message": "Payout retrieved successfully",
            "data": {
                "payout_id": payout.id,
                "gateway_payout_id": payout.gateway_payout_id,
                "amount": str(payout.amount),
                "currency": payout.currency,
                "status": payout.status,
                "method": payout.method,
                "estimated_arrival": payout.get_estimated_arrival().isoformat(),
                "created_at": payout.created_at.isoformat(),
                "processed_at": payout.processed_at.isoformat() if payout.processed_at else None,
                "failure_message": payout.failure_message
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving payout: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "An error occurred while retrieving payout"
        }), 500

@wallet_bp.route("/wallets/payment-intents", methods=["GET"])
@jwt_required()
def get_user_payment_intents():
    """
    Get all payment intents for the current user
    """
    try:
        user_id = get_jwt_identity()
        
        from app.models.payment_intent_model import PaymentIntent
        payment_intents = PaymentIntent.query.filter_by(
            user_id=user_id
        ).order_by(PaymentIntent.created_at.desc()).all()
        
        intents_data = []
        for intent in payment_intents:
            intents_data.append({
                "payment_intent_id": intent.id,
                "gateway_intent_id": intent.gateway_intent_id,
                "amount": str(intent.amount),
                "currency": intent.currency,
                "status": intent.status,
                "intent_type": intent.intent_type,
                "description": intent.description,
                "created_at": intent.created_at.isoformat(),
                "confirmed_at": intent.confirmed_at.isoformat() if intent.confirmed_at else None
            })
        
        return jsonify({
            "status": 200,
            "message": "Payment intents retrieved successfully",
            "data": intents_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving payment intents: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "An error occurred while retrieving payment intents"
        }), 500

@wallet_bp.route("/wallets/payouts", methods=["GET"])
@jwt_required()
def get_user_payouts():
    """
    Get all payouts for the current user
    """
    try:
        user_id = get_jwt_identity()
        
        payouts = Payout.query.filter_by(
            user_id=user_id
        ).order_by(Payout.created_at.desc()).all()
        
        payouts_data = []
        for payout in payouts:
            payouts_data.append({
                "payout_id": payout.id,
                "gateway_payout_id": payout.gateway_payout_id,
                "amount": str(payout.amount),
                "currency": payout.currency,
                "status": payout.status,
                "method": payout.method,
                "estimated_arrival": payout.get_estimated_arrival().isoformat(),
                "created_at": payout.created_at.isoformat(),
                "processed_at": payout.processed_at.isoformat() if payout.processed_at else None,
                "failure_message": payout.failure_message
            })
        
        return jsonify({
            "status": 200,
            "message": "Payouts retrieved successfully",
            "data": payouts_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving payouts: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "An error occurred while retrieving payouts"
        }), 500
