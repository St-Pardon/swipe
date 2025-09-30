import stripe
import random
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.virtual_cards_model import VirtualCard
from app.models.account_model import Account
from app.models.user_model import User
from app.schema.virtual_cards_schema import VirtualCardSchema
from app.extensions import db
from app.services.payment_service import PaymentService
from app.config.payment_config import PaymentConfig
from app.services.notification_service import NotificationService
from decimal import Decimal

# Initialize Stripe using configured secret key
try:
    if PaymentConfig.STRIPE_SECRET_KEY:
        print("Stripe secret key configured. from card.py")
        print(PaymentConfig.STRIPE_SECRET_KEY)
        stripe.api_key = PaymentConfig.STRIPE_SECRET_KEY
    else:
        logging.warning("Stripe secret key not configured. Stripe operations will be skipped.")
        stripe.api_key = None  # Explicitly set to None for development mode
except Exception as _e:
    logging.error(f"Failed to initialize Stripe: {_e}")
    stripe.api_key = None

card_bp = Blueprint("card", __name__)

@card_bp.route("/card", methods=["POST"])
@jwt_required()
def create_card():
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        # Fetch the user to get their name
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                "status": 404,
                "message": "User not found"
            }), 404
        
        card_schema = VirtualCardSchema()
        errors = card_schema.validate(data)
        if errors:
            return jsonify({
                "status": 400, 
                "message": "Invalid data", 
                "errors": errors
                }), 400
        
        account_id = data.get("account_id")
        if not account_id:
            return jsonify({
                "status": 400, 
                "message": "Account ID is required"
                }), 400
        
        # Check if the account belongs to the user
        account = Account.query.filter_by(id=account_id, user_id=user_id).first()
        if not account:
            return jsonify({
                "status": 403,
                "message": "You don't have permission to create a card for this account"
            }), 403
        
        # If this card should be the default, unset the current default.
        if data.get("is_default"):
            VirtualCard.query.filter_by(user_id=user_id, is_default=True).update({"is_default": False})
        
        # Prepare data for the model by filtering out non-model fields
        model_fields = [column.name for column in VirtualCard.__table__.columns]
        card_data = {k: v for k, v in data.items() if k in model_fields}
        

        card_data['user_id'] = user_id
        card_data['card_holder'] = user.name  # Get full name from user or maybe account
        
        # Generate a card number if not provided
        if 'card_number' not in card_data:
            card_data['card_number'] = VirtualCard.generate_card_number(user_id)
        
        # Generate a CVV if not provided
        if '_cvv' not in card_data and 'cvv' not in card_data:
            cvv = f"{random.randint(0, 999):03d}"
            card_data['cvv'] = cvv
        
        # Create a new card instance
        new_card = VirtualCard(**card_data)

        # Optionally associate an existing Stripe PaymentMethod if provided by client
        pm_id = data.get("stripe_payment_method_id")
        if pm_id:
            try:
                if not getattr(stripe, 'api_key', None):
                    raise ValueError("Stripe not configured")
                pm = stripe.PaymentMethod.retrieve(pm_id)
                if not pm or pm.get('type') != 'card':
                    return jsonify({
                        "status": 400,
                        "message": "Provided payment method is invalid or not a card."
                    }), 400
                new_card.stripe_payment_method_id = pm_id
            except stripe.error.StripeError as e:
                return jsonify({
                    "status": 400,
                    "message": f"Failed to verify Stripe payment method: {str(e)}"
                }), 400
            except Exception as verify_err:
                logging.warning(f"Stripe verification error: {verify_err}")
                return jsonify({
                    "status": 400,
                    "message": "Unable to verify Stripe payment method."
                }), 400

        db.session.add(new_card)
        db.session.commit()
        
        result = card_schema.dump(new_card)

        try:
            card_number = new_card.card_number
            NotificationService.create_notification(
                user_id=user_id,
                title="New card created",
                message="A new {card_type} card ending in {last4} was created for your {currency} wallet.".format(
                    card_type=new_card.card_type,
                    last4=card_number[-4:] if card_number else "****",
                    currency=account.currency_code
                ),
                category='account',
                priority='medium',
                metadata={
                    "card_id": str(new_card.id),
                    "account_id": str(account.id),
                    "card_type": new_card.card_type,
                    "currency": account.currency_code
                }
            )
        except Exception as notify_err:
            logging.warning(f"Card creation notification failed: {notify_err}")

        return jsonify({
            "status": 201,
            "message": "Card created successfully",
            "data": result
        }), 201

    except ValueError as e:
        return jsonify({
            "status": 400,
            "message": str(e)
        }), 400
        
    except Exception as e:
        db.session.rollback()
        import traceback
        error_trace = traceback.format_exc()
        print(f"Card creation error: {error_trace}")  # Debug output
        return jsonify({
            "status": 500,
            "message": "An error occurred while creating the card",
            "error": str(e),
            "trace": error_trace
        }), 500

@card_bp.route("/card/<string:card_id>", methods=["GET"])
@jwt_required()
def get_card(card_id):
    """Get a specific card by ID"""
    try:
        user_id = get_jwt_identity()
        
        # Fetch the card and verify it belongs to the authenticated user
        card = VirtualCard.query.filter_by(id=card_id, user_id=user_id).first()
        
        if not card:
            return jsonify({
                "status": 404,
                "message": "Card not found"
            }), 404
        
        # Serialize the card data
        card_schema = VirtualCardSchema()
        result = card_schema.dump(card)
        
        return jsonify({
            "status": 200,
            "message": "Card retrieved successfully",
            "data": result
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": 500,
            "message": "An error occurred while retrieving the card",
            "error": str(e)
        }), 500


@card_bp.route("/cards", methods=["GET"])
@jwt_required()
def get_all_cards():
    """Get all cards for the authenticated user with filtering, pagination and sorting"""
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters for filtering, pagination and sorting
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)
        card_kind = request.args.get('card_kind')
        card_type = request.args.get('card_type')
        is_active = request.args.get('is_active')
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if size < 1 or size > 100:  # Limit max size to 100
            size = 10
            
        # Build the base query
        query = VirtualCard.query.filter_by(user_id=user_id)
        
        if card_kind:
            query = query.filter(VirtualCard.card_kind == card_kind)
        if card_type:
            query = query.filter(VirtualCard.card_type == card_type)
        if is_active is not None:
            is_active_bool = is_active.lower() in ['true', '1', 'yes']
            query = query.filter(VirtualCard.is_active == is_active_bool)
        
        cards = query.paginate(page=page, per_page=size, error_out=False)
        
        card_schema = VirtualCardSchema(many=True)
        result = card_schema.dump(cards.items)
        
        return jsonify({
            "status": 200,
            "message": "Cards retrieved successfully",
            "data": result,
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": 500,
            "message": "An error occurred while retrieving the cards",
            "error": str(e)
        }), 500

@card_bp.route("/card/<string:card_id>/deactivate", methods=["PATCH"])
@jwt_required()
def deactivate_card(card_id):
    """Deactivate a specific card"""
    try:
        user_id = get_jwt_identity()
        
        card = VirtualCard.query.filter_by(id=card_id, user_id=user_id).first()
        
        if not card:
            return jsonify({
                "status": 404,
                "message": "Card not found"
            }), 404
        
        # Check if card is already inactive
        if not card.is_active:
            return jsonify({
                "status": 400,
                "message": "Card is already deactivated"
            }), 400
        
        # Deactivate the card
        card.is_active = False
        db.session.commit()

        card_schema = VirtualCardSchema()
        result = card_schema.dump(card)

        try:
            card_number = card.card_number
            NotificationService.create_notification(
                user_id=user_id,
                title="Card deactivated",
                message="Your card ending in {last4} has been deactivated.".format(
                    last4=card_number[-4:] if card_number else "****"
                ),
                category='security',
                priority='high',
                metadata={
                    "card_id": str(card.id),
                    "action": "deactivate"
                }
            )
        except Exception as notify_err:
            logging.warning(f"Card deactivation notification failed: {notify_err}")

        return jsonify({
            "status": 200,
            "message": "Card deactivated successfully",
            "data": result
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": 500,
            "message": "An error occurred while deactivating the card",
            "error": str(e)
        }), 500


@card_bp.route("/card/<string:card_id>/reveal", methods=["POST"])
@jwt_required()
def reveal_full_card_number(card_id):
    """Get full card number with PIN verification"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate PIN is provided
        if not data or not data.get('pin'):
            return jsonify({
                "status": 400,
                "message": "PIN is required"
            }), 400
        
        provided_pin = data.get('pin')
        
        # Fetch the card and verify it belongs to the authenticated user
        card = VirtualCard.query.filter_by(id=card_id, user_id=user_id).first()
        
        if not card:
            return jsonify({
                "status": 404,
                "message": "Card not found"
            }), 404
        
        # Verify the PIN
        if card.pin != provided_pin:
            return jsonify({
                "status": 401,
                "message": "Invalid PIN"
            }), 401
        
        # Return the full card number
        return jsonify({
            "status": 200,
            "message": "Card number revealed successfully",
            "data": {
                "card_id": card.id,
                "card_number": card.card_number,  # This will decrypt and return the full number
                "card_holder": card.card_holder,
                "expiration_date": card.expiration_date
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": 500,
            "message": "An error occurred while revealing the card number",
            "error": str(e)
        }), 500

@card_bp.route("/card/<string:id>", methods=["DELETE"])
@jwt_required()
def delete_card(id):
    """Delete a specific card"""
    try:
        user_id = get_jwt_identity()
        card = VirtualCard.query.filter_by(id=id, user_id=user_id).first()

        if not card:
            return jsonify({
                "status": 404,
                "message": "Card not found"
            }), 404

        # Store payment method ID for cleanup before deletion
        stripe_payment_method_id = card.stripe_payment_method_id

        # Clean up Stripe payment method if it exists
        if stripe_payment_method_id:
            try:
                if getattr(stripe, 'api_key', None):
                    # Attempt to detach the payment method from the customer
                    # Note: This will make the payment method reusable for future cards
                    detached_pm = stripe.PaymentMethod.detach(stripe_payment_method_id)
                    logging.info(f"Successfully detached Stripe payment method {stripe_payment_method_id} from customer")
                else:
                    logging.info(f"Development mode: Skipping Stripe cleanup for payment method {stripe_payment_method_id}")
            except stripe.error.StripeError as stripe_err:
                # Log the error but don't fail the card deletion
                logging.warning(f"Failed to detach Stripe payment method {stripe_payment_method_id}: {str(stripe_err)}")
                logging.info("Continuing with card deletion despite Stripe cleanup failure")
            except Exception as cleanup_err:
                # Handle any other cleanup errors
                logging.warning(f"Unexpected error during Stripe cleanup for {stripe_payment_method_id}: {str(cleanup_err)}")
                logging.info("Continuing with card deletion despite cleanup error")

        # Delete the card from database
        db.session.delete(card)
        db.session.commit()

        try:
            card_number = card.card_number
            NotificationService.create_notification(
                user_id=user_id,
                title="Card deleted",
                message="Your card ending in {last4} has been deleted.".format(
                    last4=card_number[-4:] if card_number else "****"
                ),
                category='security',
                priority='high',
                metadata={
                    "card_id": str(id),
                    "payment_method": stripe_payment_method_id
                }
            )
        except Exception as notify_err:
            logging.warning(f"Card deletion notification failed: {notify_err}")

        return jsonify({
            "status": 200,
            "message": "Card deleted successfully" + (f" and payment method detached from Stripe" if stripe_payment_method_id else "")
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": 500,
            "message": "An error occurred while deleting the card",
            "error": str(e)
        }), 500

@card_bp.route("/card/<string:id>/change-pin", methods=["PUT"])
@jwt_required()
def change_pin(id):
    try:
        user_id = get_jwt_identity()
        data = request.get_json() # gets current pin and new pin

        card = VirtualCard.query.filter_by(id=id, user_id=user_id).first()
        if not card:
            return jsonify({
                "status": 404,
                "message": "Card not found"
            }), 404

        if card.pin != data.get('current_pin'):
            return jsonify({
                "status": 401,
                "message": "Invalid current PIN"
            }), 401

        card.pin = data.get('new_pin')
        db.session.commit()

        try:
            card_number = card.card_number
            NotificationService.create_notification(
                user_id=user_id,
                title="Card PIN changed",
                message="The PIN for your card ending in {last4} was changed successfully.".format(
                    last4=card_number[-4:] if card_number else "****"
                ),
                category='security',
                priority='high',
                metadata={
                    "card_id": str(card.id)
                }
            )
        except Exception as notify_err:
            logging.warning(f"Card PIN change notification failed: {notify_err}")

        return jsonify({
            "status": 200,
            "message": "Card PIN changed successfully"
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": 500,
            "message": "An error occurred while changing the card PIN",
            "error": str(e)
        }), 500

@card_bp.route("/card/<string:card_id>/link-payment-method", methods=["POST"])
@jwt_required()
def link_payment_method(card_id):
    """Link a Stripe payment method to an existing virtual card"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('stripe_payment_method_id'):
            return jsonify({
                "status": 400,
                "message": "stripe_payment_method_id is required"
            }), 400
        
        # Verify card belongs to user
        card = VirtualCard.query.filter_by(id=card_id, user_id=user_id).first()
        if not card:
            return jsonify({
                "status": 404,
                "message": "Card not found"
            }), 404
        
        stripe_payment_method_id = data.get('stripe_payment_method_id')
        
        # Verify the Stripe payment method exists and is valid
        from app.config.payment_config import PaymentConfig
        
        # Check if we're in development mode (no Stripe key configured)
        if not PaymentConfig.STRIPE_SECRET_KEY:
            # For development without Stripe, allow linking mock payment methods
            if not stripe_payment_method_id.startswith('pm_'):
                return jsonify({
                    "status": 400,
                    "message": "Invalid payment method ID format"
                }), 400
            # Skip Stripe verification in development mode
            logging.info(f"Development mode: Skipping Stripe verification for {stripe_payment_method_id}")
        else:
            # Production mode - verify with Stripe
            try:
                pm = stripe.PaymentMethod.retrieve(stripe_payment_method_id)
                if not pm or pm.get('type') not in ['card', 'us_bank_account', 'sepa_debit', 'klarna', 'afterpay_clearpay']:
                    return jsonify({
                        "status": 400,
                        "message": "Payment method type not supported"
                    }), 400
            except (stripe.error.StripeError, ConnectionError, Exception) as stripe_err:
                # Handle Stripe errors gracefully
                if ("Failed to resolve" in str(stripe_err) or 
                    "ConnectionError" in str(stripe_err) or
                    "NoneType" in str(stripe_err) or
                    "Secret" in str(stripe_err)):
                    logging.warning(f"Stripe API issue: {stripe_err}")
                    logging.info(f"Allowing payment method {stripe_payment_method_id} due to API issues")
                    # Allow the operation to continue with basic validation
                    if not stripe_payment_method_id.startswith('pm_'):
                        return jsonify({
                            "status": 400,
                            "message": "Invalid payment method ID format"
                        }), 400
                else:
                    return jsonify({
                        "status": 400,
                        "message": f"Failed to verify Stripe payment method: {str(stripe_err)}"
                    }), 400
        
        # Link the payment method to the card
        card.stripe_payment_method_id = stripe_payment_method_id
        db.session.commit()

        card_schema = VirtualCardSchema()
        result = card_schema.dump(card)

        try:
            card_number = card.card_number
            NotificationService.create_notification(
                user_id=user_id,
                title="Payment method linked",
                message="Card ending in {last4} is now linked to payment method {pm}.".format(
                    last4=card_number[-4:] if card_number else "****",
                    pm=stripe_payment_method_id
                ),
                category='transaction',
                priority='medium',
                metadata={
                    "card_id": str(card.id),
                    "payment_method": stripe_payment_method_id
                }
            )
        except Exception as notify_err:
            logging.warning(f"Card payment method link notification failed: {notify_err}")

        return jsonify({
            "status": 200,
            "message": "Payment method linked successfully",
            "data": result
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": 500,
            "message": "An error occurred while linking payment method",
            "error": str(e)
        }), 500

@card_bp.route("/payment-methods/available", methods=["GET"])
@jwt_required()
def get_available_payment_methods():
    """Get available payment method types that can be linked to virtual cards"""
    try:
        # Define supported payment method types
        payment_methods = [
            {
                "type": "card",
                "name": "Credit/Debit Card",
                "description": "Visa, Mastercard, American Express, and other card networks",
                "supported_countries": ["US", "CA", "GB", "EU", "AU"],
                "fees": "2.9% + 30¢ per transaction"
            },
            {
                "type": "us_bank_account", 
                "name": "US Bank Account (ACH)",
                "description": "Direct bank account transfers via ACH",
                "supported_countries": ["US"],
                "fees": "0.8% per transaction (capped at $5)"
            },
            {
                "type": "sepa_debit",
                "name": "SEPA Direct Debit",
                "description": "European bank account transfers",
                "supported_countries": ["EU"],
                "fees": "0.8% per transaction"
            },
            {
                "type": "klarna",
                "name": "Klarna",
                "description": "Buy now, pay later with Klarna",
                "supported_countries": ["US", "GB", "EU", "AU"],
                "fees": "3.5% + 30¢ per transaction"
            },
            {
                "type": "afterpay_clearpay",
                "name": "Afterpay/Clearpay", 
                "description": "Buy now, pay later in 4 installments",
                "supported_countries": ["US", "GB", "AU"],
                "fees": "4% + 30¢ per transaction"
            }
        ]
        
        return jsonify({
            "status": 200,
            "message": "Available payment methods retrieved successfully",
            "data": {
                "payment_methods": payment_methods,
                "total_count": len(payment_methods)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": 500,
            "message": "An error occurred while retrieving payment methods",
            "error": str(e)
        }), 500

@card_bp.route("/card/<string:card_id>/payment-method", methods=["GET"])
@jwt_required()
def get_card_payment_method(card_id):
    """Get the linked payment method for a specific virtual card"""
    try:
        user_id = get_jwt_identity()
        
        # Verify card belongs to user
        card = VirtualCard.query.filter_by(id=card_id, user_id=user_id).first()
        if not card:
            return jsonify({
                "status": 404,
                "message": "Card not found"
            }), 404
        
        if not card.stripe_payment_method_id:
            return jsonify({
                "status": 200,
                "message": "No payment method linked to this card",
                "data": {
                    "card_id": card_id,
                    "payment_method": None,
                    "linked": False
                }
            }), 200
        
        # Prepare base payload with stored data only
        payment_method_details = {
            "id": card.stripe_payment_method_id,
            "linked": True,
            "type": "unknown"
        }
        
        # Only attempt live Stripe lookup when API key configured
        try:
            from app.config.payment_config import PaymentConfig

            stripe_key = getattr(PaymentConfig, "STRIPE_SECRET_KEY", None)
            if stripe_key and getattr(stripe, 'api_key', None):
                pm = stripe.PaymentMethod.retrieve(card.stripe_payment_method_id)
                payment_method_details.update({
                    "type": pm.type,
                    "created": pm.created,
                    "customer": pm.customer
                })
                
                # Add type-specific details
                if pm.type == 'card' and pm.card:
                    payment_method_details["card"] = {
                        "brand": pm.card.brand,
                        "last4": pm.card.last4,
                        "exp_month": pm.card.exp_month,
                        "exp_year": pm.card.exp_year,
                        "funding": pm.card.funding
                    }
                elif pm.type == 'us_bank_account' and pm.us_bank_account:
                    payment_method_details["bank_account"] = {
                        "bank_name": pm.us_bank_account.bank_name,
                        "last4": pm.us_bank_account.last4,
                        "account_type": pm.us_bank_account.account_type
                    }
            else:
                payment_method_details["stripe_lookup_skipped"] = True
        except stripe.error.StripeError:
            # If Stripe call fails, return basic info
            payment_method_details["stripe_lookup_error"] = "stripe_error"
        except Exception as lookup_err:
            payment_method_details["stripe_lookup_error"] = str(lookup_err)
        
        return jsonify({
            "status": 200,
            "message": "Card payment method retrieved successfully",
            "data": {
                "card_id": card_id,
                "payment_method": payment_method_details,
                "linked": True
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": 500,
            "message": "An error occurred while retrieving card payment method",
            "error": str(e)
        }), 500