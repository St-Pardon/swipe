from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.account_model import Account
from app.schema.account_schema import AccountSchema
from app.extensions import db


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

        return jsonify({
            "status": 200,
            "message": "Account updated successfully",
            "data": result
        }), 200
    except Exception as e:
        db.session.rollback()
        # It's good practice to log the error here
        return jsonify({"status": 500, "message": str(e)}), 500

