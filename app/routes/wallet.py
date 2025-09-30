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
from app.routes.transaction import create_transaction
from app.services.notification_service import NotificationService

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
        # Log transaction as pending intent (credit to account on success)
        try:
            create_transaction(
                user_id=user_id,
                txn_type="wallet_fund_intent",
                status="pending",
                amount=amount,
                currency_code=currency,
                description=description or f"Wallet funding intent {payment_intent.id}",
                credit_account_id=account_id,
                metadata={
                    "payment_intent_id": str(payment_intent.id),
                },
            )
            db.session.commit()
        except Exception:
            db.session.rollback()
            # Do not fail primary flow on logging failure
        
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
        
        try:
            NotificationService.create_notification(
                user_id=user_id,
                title="Wallet funding initiated",
                message=f"We have started funding your wallet with {amount} {currency}.",
                category='transaction',
                priority='medium',
                metadata={
                    "payment_intent_id": str(payment_intent.id),
                    "account_id": str(account_id),
                    "amount": str(amount),
                    "currency": currency
                }
            )
        except Exception as notify_err:
            logger.warning(f"Wallet funding notification failed: {notify_err}")
        
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
        required_fields = ['amount', 'currency']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": 400,
                    "message": f"Missing required field: {field}"
                }), 400
        
        # account_number is required for withdrawal (external bank account)
        account_number = data.get('account_number')
        
        if not account_number:
            return jsonify({
                "status": 400,
                "message": "account_number is required for withdrawal"
            }), 400
        
        amount = Decimal(str(data['amount']))
        currency = data['currency'].upper()
        account_id = data.get('account_id')
        method = data.get('method', 'standard')  # standard or instant
        
        # Validate that the account_number exists and belongs to user
        from app.models.account_model import Account
        target_account = None
        for account in Account.query.filter_by(user_id=user_id).all():
            if account.get_account_number() == account_number:
                target_account = account
                break
        
        if not target_account:
            return jsonify({
                "status": 404,
                "message": f"No account found with account number: {account_number}"
            }), 404
        
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
        
        # Create payout using PaymentService (withdrawal to external bank)
        payout = PaymentService.create_withdrawal(
            user_id=user_id,
            source_account_id=account_id,
            target_account_number=account_number,
            amount=amount,
            currency=currency,
            method=method
        )
        # Log payout transaction as pending (debit from account)
        try:
            create_transaction(
                user_id=user_id,
                txn_type="payout",
                status="pending",
                amount=amount,
                currency_code=currency,
                description=f"Withdrawal to account {account_number}",
                debit_account_id=account_id,
                metadata={
                    "payout_id": str(payout.id),
                    "method": method,
                },
            )
            db.session.commit()
        except Exception:
            db.session.rollback()
            # Non-critical if logging fails
        
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
        
        try:
            NotificationService.create_notification(
                user_id=user_id,
                title="Withdrawal initiated",
                message=f"A withdrawal of {amount} {currency} to account {account_number[-4:]} has been initiated.",
                category='transaction',
                priority='high',
                metadata={
                    "payout_id": str(payout.id),
                    "account_id": str(account_id),
                    "amount": str(amount),
                    "currency": currency,
                    "method": method
                }
            )
        except Exception as notify_err:
            logger.warning(f"Withdrawal notification failed: {notify_err}")
        
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

@wallet_bp.route("/wallets/transfer", methods=["POST"])
@jwt_required()
def transfer_funds():
    """
    Transfer funds between accounts (beneficiaries, second accounts, other customers, non-customers)
    """
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        # Validate required fields
        required_fields = ['amount', 'currency', 'transfer_type']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": 400,
                    "message": f"Missing required field: {field}"
                }), 400
        
        amount = Decimal(str(data['amount']))
        currency = data['currency'].upper()
        transfer_type = data['transfer_type']  # 'beneficiary', 'internal', 'customer', 'external'
        source_account_id = data.get('source_account_id')
        description = data.get('description', '')
        
        # If no source_account_id provided, use default account
        if not source_account_id:
            default_account = Account.query.filter_by(
                user_id=user_id, 
                is_default=True,
                currency_code=currency
            ).first()
            
            if not default_account:
                return jsonify({
                    "status": 404,
                    "message": f"No default {currency} account found. Please specify source_account_id."
                }), 404
            
            source_account_id = default_account.id
        
        # Validate currency support
        if not PaymentConfig.is_payout_currency_supported(currency):
            return jsonify({
                "status": 400,
                "message": f"Currency {currency} is not supported for transfers"
            }), 400
        
        # Handle different transfer types
        if transfer_type == 'beneficiary':
            # Transfer to beneficiary account
            beneficiary_id = data.get('beneficiary_id')
            if not beneficiary_id:
                return jsonify({
                    "status": 400,
                    "message": "beneficiary_id is required for beneficiary transfers"
                }), 400
            
            transfer = PaymentService.create_beneficiary_transfer(
                user_id=user_id,
                source_account_id=source_account_id,
                beneficiary_id=beneficiary_id,
                amount=amount,
                currency=currency,
                description=description
            )
            
        elif transfer_type == 'internal':
            # Transfer to another account owned by the same user
            target_account_id = data.get('target_account_id')
            if not target_account_id:
                return jsonify({
                    "status": 400,
                    "message": "target_account_id is required for internal transfers"
                }), 400
            
            transfer = PaymentService.create_internal_transfer(
                user_id=user_id,
                source_account_id=source_account_id,
                target_account_id=target_account_id,
                amount=amount,
                currency=currency,
                description=description
            )
            
        elif transfer_type == 'customer':
            # Transfer to another customer's account
            target_user_email = data.get('target_user_email')
            target_account_number = data.get('target_account_number')
            
            if not target_user_email and not target_account_number:
                return jsonify({
                    "status": 400,
                    "message": "Either target_user_email or target_account_number is required for customer transfers"
                }), 400
            
            transfer = PaymentService.create_customer_transfer(
                user_id=user_id,
                source_account_id=source_account_id,
                target_user_email=target_user_email,
                target_account_number=target_account_number,
                amount=amount,
                currency=currency,
                description=description
            )
            
        elif transfer_type == 'external':
            # Transfer to external account (non-customer)
            target_account_number = data.get('target_account_number')
            target_routing_number = data.get('target_routing_number')
            target_bank_name = data.get('target_bank_name')
            target_account_holder = data.get('target_account_holder')
            
            required_external_fields = ['target_account_number', 'target_routing_number', 'target_bank_name', 'target_account_holder']
            for field in required_external_fields:
                if field not in data:
                    return jsonify({
                        "status": 400,
                        "message": f"Missing required field for external transfer: {field}"
                    }), 400
            
            transfer = PaymentService.create_external_transfer(
                user_id=user_id,
                source_account_id=source_account_id,
                target_account_number=target_account_number,
                target_routing_number=target_routing_number,
                target_bank_name=target_bank_name,
                target_account_holder=target_account_holder,
                amount=amount,
                currency=currency,
                description=description
            )
            
        else:
            return jsonify({
                "status": 400,
                "message": "Invalid transfer_type. Must be one of: beneficiary, internal, customer, external"
            }), 400
        
        # Log transfer transaction
        try:
            create_transaction(
                user_id=user_id,
                txn_type="transfer",
                status="pending",
                amount=amount,
                currency_code=currency,
                description=description or f"Transfer ({transfer_type})",
                debit_account_id=source_account_id,
                metadata={
                    "transfer_id": str(transfer.id),
                    "transfer_type": transfer_type,
                },
            )
            db.session.commit()
        except Exception:
            db.session.rollback()
            # Non-critical if logging fails
        
        return jsonify({
            "status": 201,
            "message": "Transfer initiated successfully",
            "data": {
                "transfer_id": transfer.id,
                "gateway_transfer_id": getattr(transfer, 'gateway_payout_id', None),
                "amount": str(transfer.amount),
                "currency": transfer.currency,
                "status": transfer.status,
                "transfer_type": transfer_type,
                "estimated_arrival": transfer.get_estimated_arrival().isoformat() if hasattr(transfer, 'get_estimated_arrival') else None
            }
        }), 201
        
        try:
            NotificationService.create_notification(
                user_id=user_id,
                title="Transfer initiated",
                message=f"Your {transfer_type} transfer of {amount} {currency} has been initiated.",
                category='transaction',
                priority='medium',
                metadata={
                    "transfer_id": str(transfer.id),
                    "transfer_type": transfer_type,
                    "source_account_id": str(source_account_id),
                    "amount": str(amount),
                    "currency": currency
                }
            )
        except Exception as notify_err:
            logger.warning(f"Transfer notification failed: {notify_err}")
        
    except ValueError as e:
        return jsonify({
            "status": 400,
            "message": str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error creating transfer: {str(e)}")
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
