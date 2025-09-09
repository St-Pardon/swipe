from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError
from app.extensions import db
from app.models.user_model import User
from app.schema.user_schema import User_schema


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
        
        user_schema = User_schema()
        updated_user = user_schema.load(data, instance=user, partial=True)

        db.session.commit()

        result = user_schema.dump(updated_user)
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
    

