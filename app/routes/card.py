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
from app.config.payment_config import PaymentConfig
from app.services.payment_service import PaymentService
from app.config.payment_config import PaymentConfig
from decimal import Decimal

# Initialize Stripe using configured secret key
try:
    if getattr(PaymentConfig, 'STRIPE_SECRET_KEY', None):
        stripe.api_key = PaymentConfig.STRIPE_SECRET_KEY
    else:
        logging.warning("Stripe secret key not configured. Stripe operations will be skipped.")
except Exception as _e:
    logging.error(f"Failed to initialize Stripe: {_e}")

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

        db.session.add(new_card)
        db.session.commit()
        
        result = card_schema.dump(new_card)
        
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

        db.session.delete(card)
        db.session.commit()

        return jsonify({
            "status": 200,
            "message": "Card deleted successfully"
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": 500,
            "message": "An error occurred while revealing the card number",
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