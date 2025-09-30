from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.decorator import role_required
from app.models.account_model import Account
from app.models.user_model import User
from app.schema.account_schema import AccountSchema, VALID_CURRENCY_CODES
from app.extensions import db
from app.utils.xconverter import apply_margins, fetch_exchange_rates, get_exchange_rate
from app.services.notification_service import NotificationService


account_bp = Blueprint('account', __name__)

@account_bp.route("/accounts", methods=["POST"])
@jwt_required()
def create_account():
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        account_schema = AccountSchema()

        # Validate the incoming data first
        errors = account_schema.validate(data)
        if errors:
            return jsonify({"status": 400, "message": "Invalid data", "errors": errors}), 400
        
        # If this account should be the default, unset the current default.
        if data.get("is_default"):
            Account.query.filter_by(user_id=user_id, is_default=True).update({"is_default": False})

        bank_code = data.get("bank_code", "2025")

        # Prepare data for the model by filtering out non-model fields
        loadable_fields = {k for k, v in account_schema.fields.items() if not v.dump_only}
        account_data = {k: v for k, v in data.items() if k in loadable_fields}

        # Ensure user_id from JWT is used, not from request body, to prevent TypeError.
        if 'user_id' in account_data:
            del account_data['user_id']

        # Use the robust class method to create the account instance
        account = Account.create_account(
            user_id=user_id,
            bank_code=bank_code,
            **account_data
        )

        # Commit the transaction to save the new account and the 'is_default' update
        db.session.commit()

        result = account_schema.dump(account)

        try:
            account_number = account.get_account_number()
            NotificationService.create_notification(
                user_id=user_id,
                title="New account created",
                message=f"Your {account.currency_code} account"
                        f"{' ending in ' + account_number[-4:] if account_number else ''}"
                        " was created successfully.",
                category='account',
                priority='medium',
                metadata={
                    "account_id": str(account.id),
                    "balance": str(account.balance),
                    "currency": account.currency_code
                }
            )
        except Exception as notify_err:
            current_app.logger.warning(f"Account creation notification failed: {notify_err}")

        return jsonify({
            "status": 201,
            "message": "Account created successfully",
            "data": result
        }), 201
    
    except Exception as e:
        db.session.rollback()
        # It's good practice to log the error here
        return jsonify({"status": 500, "message": str(e)}), 500


@account_bp.route("/accounts", methods=["GET"])
@jwt_required()
def get_accounts():
    """Retrieve all accounts for the logged-in user."""
    try:
        user_id = get_jwt_identity()
        accounts = Account.query.filter_by(user_id=user_id).order_by(Account.created_at.desc()).all()
        
        if not accounts:
            return jsonify({
                "status": 200,
                "message": "No accounts found for this user.",
                "data": []
            }), 200

        account_schema = AccountSchema(many=True)
        result = account_schema.dump(accounts)

        return jsonify({
            "status": 200,
            "message": "Accounts retrieved successfully",
            "data": result
        }), 200
    except Exception as e:
        # It's good practice to log the error here
        return jsonify({"status": 500, "message": str(e)}), 500

@account_bp.route("/accounts/<string:id>", methods=["GET"])
@jwt_required()
def get_account(id):
    """Retrieve a specific account for the logged-in user."""
    try:
        user_id = get_jwt_identity()
        account = Account.query.filter_by(user_id=user_id, id=id).first()

        if not account:
            return jsonify({
                "status": 404,
                "message": "Account not found"
            }), 404
        
        account_schema = AccountSchema()
        result = account_schema.dump(account)

        return jsonify({
            "status": 200,
            "message": "Account retrieved successfully",
            "data": result
        }), 200

    except Exception as e:
        # It's good practice to log the error here
        return jsonify({"status": 500, "message": str(e)}), 500

@account_bp.route("/accounts/<string:id>", methods=["PUT"])
@jwt_required()
def update_account(id):
    """Update a specific account for the logged-in user."""
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        account_schema = AccountSchema()

        account = Account.query.filter_by(user_id=user_id, id=id).first()

        if not account:
            return jsonify({
                "status": 404,
                "message": "Account not found"
            }), 404
        
        # Validate the incoming data
        errors = account_schema.validate(data, partial=True) # partial=True allows partial updates
        if errors:
            return jsonify({"status": 400, "message": "Invalid data", "errors": errors}), 400

        # If the update includes setting this account as default, unset others
        if data.get("is_default") is True:
            Account.query.filter_by(user_id=user_id, is_default=True).filter(Account.id != id).update({"is_default": False})
            db.session.commit() # Commit this update before loading the current account

        # Load the data into the existing account object
        updated_account = account_schema.load(data, instance=account, partial=True)
        db.session.commit()

        result = account_schema.dump(updated_account)

        try:
            account_number = updated_account.get_account_number()
            NotificationService.create_notification(
                user_id=user_id,
                title="Account updated",
                message=f"Your {updated_account.currency_code} account"
                        f"{' ending in ' + account_number[-4:] if account_number else ''}"
                        " was updated successfully.",
                category='account',
                priority='low',
                metadata={
                    "account_id": str(updated_account.id),
                    "updated_fields": list(data.keys())
                }
            )
        except Exception as notify_err:
            current_app.logger.warning(f"Account update notification failed: {notify_err}")

        return jsonify({
            "status": 200,
            "message": "Account updated successfully",
            "data": result
        }), 200
    except Exception as e:
        db.session.rollback()
        # It's good practice to log the error here
        return jsonify({"status": 500, "message": str(e)}), 500

@account_bp.route("/balances", methods=["GET"])
@jwt_required()
def get_balances():
    """Retrieve all balances for the logged-in user from their various accounts."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                "status": 404,
                "message": "User not found"
            }), 404
            
        accounts = Account.query.filter_by(user_id=user_id).all()
        balances = {}
        for account in accounts:
            currency = account.currency_code.lower()
            balances[currency] = balances.get(currency, 0) + account.balance
            
        # Determine the currency of the default account
        default_account = Account.query.filter_by(user_id=user_id, is_default=True).first()
        default_currency = default_account.currency_code.lower() if default_account else None
        
        # Calculate total in default currency
        total_in_default = 0.0
        if default_currency:
            for currency, balance in balances.items():
                if currency == default_currency:
                    total_in_default += balance
                else:
                    rate = get_exchange_rate(currency, default_currency)
                    print(f"DEBUG: Converting {currency} to {default_currency} - Rate: {rate}")
                    if rate is not None:
                        total_in_default += balance * rate
                    else:
                        print(f"Could not get exchange rate for {currency} to {default_currency}")
        
        # Prepare response data
        response_data = {}
        for currency, balance in balances.items():
            response_data[currency] = str(balance)
            
        response_data["currency"] = default_account.currency_code if default_account else None
        response_data["total"] = str(round(total_in_default, 2)) if default_currency else None
        
        return jsonify({
            "status": 200,
            "message": "All balances retrieved successfully",
            "data": response_data
        }), 200
    except Exception as e:
        return jsonify({"status": 500, "message": str(e)}), 500

@account_bp.route('/rates', methods=['GET'])
@jwt_required(optional=True)
def get_exchange_rates():
    """Retrieve current exchange rates with applied margins"""
    try:
        base_currency = request.args.get('base')
        user_id = get_jwt_identity()

        if not base_currency:
            if user_id:
                # If user is logged in, try to get their default account's currency
                default_account = Account.query.filter_by(user_id=user_id, is_default=True).first()
                if default_account:
                    base_currency = default_account.currency_code
            
            # Fallback to USD if no base currency is determined
            if not base_currency:
                base_currency = "USD"
        
        base_currency = base_currency.upper()
        
        # Fetch exchange rates (from cache or API)
        rates = fetch_exchange_rates(base_currency)
        if rates is None:
            return jsonify({
                "status": 500,
                "message": "Failed to fetch exchange rates from provider"
            }), 500
        
        # Apply margins and format rates for all supported currencies
        formatted_rates = apply_margins(rates, base_currency, VALID_CURRENCY_CODES)
        
        # Prepare response
        response_data = {
            "currency": base_currency,
            "rates": formatted_rates
        }
        
        return jsonify({
            "status": 200,
            "message": "Retrieved current exchange rates successfully",
            "data": response_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Unexpected error in get_exchange_rates: {str(e)}")
        return jsonify({
            "status": 500,
            "message": "An unexpected error occurred"
        }), 500

@account_bp.route("/wallets/balance", methods=["GET"])
@jwt_required()
def get_default_account_balance():
    """Retrieve balance and currency for the user's default account."""
    try:
        user_id = get_jwt_identity()
        
        # Find the default account for the user
        default_account = Account.query.filter_by(user_id=user_id, is_default=True).first()
        
        if not default_account:
            return jsonify({
                "status": 404,
                "message": "No default account found for this user."
            }), 404

        response_data = {
            "balance": default_account.balance,
            "currency": default_account.currency_code
        }

        return jsonify({
            "status": 200,
            "message": "Default account balance retrieved successfully",
            "data": response_data
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error in get_default_account_balance: {str(e)}")
        return jsonify({"status": 500, "message": "An error occurred while retrieving the balance."}), 500

@account_bp.route("/account/close", methods=["POST"])
@role_required("admin")
def close_account():
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        account = Account.query.filter_by(user_id=user_id, id=data["account_id"]).first()
        if not account:
            return jsonify({
                "status": 404,
                "message": "Account not found"
            }), 404

        account_number = account.get_account_number()
        account_currency = account.currency_code

        db.session.delete(account)
        db.session.commit()

        try:
            NotificationService.create_notification(
                user_id=user_id,
                title="Account closed",
                message=f"Your {account_currency} account"
                        f"{' ending in ' + account_number[-4:] if account_number else ''}"
                        " has been closed by an administrator.",
                category='account',
                priority='high',
                metadata={
                    "account_id": str(data["account_id"])
                }
            )
        except Exception as notify_err:
            current_app.logger.warning(f"Account closure notification failed: {notify_err}")

        return jsonify({
            "status": 200,
            "message": "Account closed successfully"
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error in close_account: {str(e)}")
        db.session.rollback()
        return jsonify({"status": 500, "message": "An error occurred while closing the account."}), 500
    
