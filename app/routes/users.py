from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError
from sqlalchemy import or_
from app.extensions import db
from app.models.user_model import User
from app.schema.user_schema import User_schema
from app.schema.beneficiaries_schema import BeneficiariesSchema
from app.models.beneficiaries_model import Beneficiaries


user_bp = Blueprint('user', __name__)

# Get Users
@user_bp.route("/users", methods=["GET"])
@jwt_required()
def get_users():
    """Retrieve all users."""
    try:
        users = User.query.all()
        user_schema = User_schema(many=True)
        result = user_schema.dump(users)

        return jsonify({
            "status": 200,
            "message": "Users retrieved successfully",
            "data": result
        })
    except Exception as e:
        return jsonify({"status": 500, "message": str(e)}), 500


# Get User
@user_bp.route("/user", methods=["GET"])
@jwt_required()
def get_user():
    """Retrieve a specific user."""
    try:
        id = request.args.get('id')
        id = id if id else get_jwt_identity()
        user = User.query.get(id)
        if not user:
            return jsonify({
                "status": 404,
                "message": "User not found"
            }), 404
        
        user_schema = User_schema()
        result = user_schema.dump(user)

        return jsonify({
            "status": 200,
            "message": "user retrieved successfully",
            "data": result
        })
    except Exception as e:
        return jsonify({"status": 500, "message": str(e)}), 500
    

# Update User
@user_bp.route("/user", methods=["PUT"])
@jwt_required()
def update_user():
    """Update user information"""
    try:
        id = request.args.get('id')
        data = request.get_json()
        if not data:
            return jsonify({
                "status": 400,
                "message": "No input data provided"
            }), 400

        id = id if id else get_jwt_identity()
        user = User.query.get(id)

        if not user:
            return jsonify({
                "status": 404,
                "message": "User not found"
            })
        
        # Update user fields directly without schema post_load
        for key, value in data.items():
            if hasattr(user, key) and key != 'password':
                setattr(user, key, value)
            elif key == 'password':
                user.set_password(value)

        db.session.commit()

        user_schema = User_schema()
        result = user_schema.dump(user)
        return jsonify({
            "status": 200,
            "message": "User updated successfully",
            "data": result
        }), 200

    except ValidationError as err:
        return jsonify({
            "status": 400,
            "message": "Validation error",
            "errors": err.messages
        }), 400

    except Exception as e:
        return jsonify({
            "status": 500,
            "message": "An error occurred while updating the user",
            "error": str(e)
        }), 500


# Delete User
@user_bp.route("/user", methods=["DELETE"])
@jwt_required()
def delete_user():
    """Delete a specific user."""
    try:
        id = request.args.get('id')
        id = id if id else get_jwt_identity()
        user = User.query.get(id)

        if not user:
            return jsonify({
                "status": 404,
                "message": "User not found"
            }), 404

        user_to_delete = User.query.get(id)
        if not user_to_delete:
            return jsonify({
                "status": 404,
                "message": "User not found"
            }), 404

        db.session.delete(user_to_delete)
        db.session.commit()

        return jsonify({
            "status": 200,
            "message": "User deleted successfully"
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": 500,
            "message": "An error occurred while deleting the user",
            "error": str(e)
        }), 500
    
# add benefitiary
@user_bp.route("/user/<string:id>/beneficiaries", methods=["POST"])
@jwt_required()
def create_benefitiary(id):
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        beneficiary_schema = BeneficiariesSchema()
        
        # Remove user_id from data if present to avoid duplicate parameter
        data.pop('user_id', None)
        
        errors = beneficiary_schema.validate(data)

        if errors:
            return jsonify({"status": 400, "message": "Invalid data", "errors": errors}), 400

        beneficiary = Beneficiaries.create_beneficiary(user_id=user_id, **data)
        db.session.add(beneficiary)
        db.session.commit()

        result = beneficiary_schema.dump(beneficiary)

        return jsonify({
            "status": 201, 
            "message": "Beneficiary created successfully", 
            "data": result
            }), 201
    except ValidationError as ve:
        return jsonify({
            "status": 400, 
            "message": "Validation error", 
            "errors": ve.messages
            }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": 500, 
            "message": "An error occurred while creating the beneficiary", 
            "error": str(e)
            }), 500

# get beneficiaries
@user_bp.route("/user/<string:id>/beneficiaries", methods=["GET"])
@jwt_required()
def get_beneficiaries(id):
    try:
        user_id = get_jwt_identity()
        
        page = request.args.get('page', default=0, type=int)
        size = request.args.get('size', default=10, type=int)
        search = request.args.get('search', default='', type=str)
        
        query = Beneficiaries.query.filter_by(user_id=user_id)
        
        if search:
            query = query.filter(or_(
                Beneficiaries.beneficiary_name.ilike(f'%{search}%'),
                Beneficiaries.bank_name.ilike(f'%{search}%'),
                Beneficiaries.account_number.ilike(f'%{search}%')
            ))
        
        # Apply pagination
        beneficiaries = query.paginate(page=page, per_page=size, error_out=False)
        
        beneficiary_schema = BeneficiariesSchema(many=True)
        result = beneficiary_schema.dump(beneficiaries.items)
        
        return jsonify({
            "status": 200, 
            "message": "Beneficiaries retrieved successfully", 
            "data": result,
            "pagination": {
                "page": page,
                "size": size,
                "total": beneficiaries.total,
                "pages": beneficiaries.pages
            }
        }), 200
    except Exception as e:
        return jsonify({
            "status": 500, 
            "message": "An error occurred while retrieving the beneficiaries", 
            "error": str(e)
        }), 50

# get beneficiary by id
@user_bp.route("/user/<string:id>/beneficiaries/<string:beneficiary_id>", methods=["GET"])
@jwt_required()
def get_beneficiary(id, beneficiary_id):
    try:
        user_id = get_jwt_identity()
        beneficiary = Beneficiaries.query.filter_by(user_id=user_id, id=beneficiary_id).first
        beneficiary_schema = BeneficiariesSchema()
        result = beneficiary_schema.dump(beneficiary)

        return jsonify({
            "status": 200, 
            "message": "Beneficiary retrieved successfully", 
            "data": result
            }), 200
    
    except Exception as e:
        return jsonify({
            "status": 500,
            "message": "An error occurred while retrieving the beneficiary",
            "error": str(e)
            }), 500
        
# update beneficiary
@user_bp.route("/beneficiary/<string:beneficiary_id>", methods=["PUT"])
@jwt_required()
def update_beneficiary(id, beneficiary_id):
    try:
        data = request.get_json()
        user_id = get_jwt_identity()

        beneficiary = Beneficiaries.query.filter_by(id=beneficiary_id, user_id=user_id).first
        if not beneficiary:
            return jsonify({
                "status": 404,
                "message": "Beneficiary not found"
            }), 404
        
        beneficiary_schema = BeneficiariesSchema()
        updated_beneficiary = beneficiary_schema.load(data, instance=beneficiary, partial=True)

        db.session.commit()

        result = beneficiary_schema.dump(updated_beneficiary)
        return jsonify({
            "status": 200,
            "message": "Beneficiary updated successfully",
            "data": result
        }), 200

    except ValidationError as err:
        return jsonify({
            "status": 400,
            "message": "Validation error",
            "errors": err.messages
        }), 400
    
    except Exception as e:
        return jsonify({
            "status": 500,
            "message": "An error occurred while updating the beneficiary",
            "error": str(e)
        }), 500



# delete beneficiary
@user_bp.route("/user/<string:id>/beneficiary/<string:beneficiary_id>", methods=["DELETE"])
@jwt_required()
def delete_beneficiary(id, beneficiary_id):
    try:
        user_id = get_jwt_identity()
        beneficiary = Beneficiaries.query.filter_by(id=beneficiary_id, user_id=user_id).first
        if not beneficiary:
            return jsonify({
                "status": 404,
                "message": "Beneficiary not found"
            }), 404

        
        db.session.delete(beneficiary)
        db.session.commit()

        return jsonify({
            "status": 200,
            "message": "Beneficiary deleted successfully"
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": 500,
            "message": "An error occurred while deleting the beneficiary",
            "error": str(e)
        }), 500

