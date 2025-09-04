from flask import Blueprint, jsonify, request
from models.user_model import User
from extensions import db
from schema.user_schema import User_schema

user_schema = User_schema()

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    try:
        user = user_schema.load(data)
    except Exception as e:
        return jsonify({"status": 400,
                        "message": "Invalid data",
                        "error": str(e)}), 400

    if User.query.filter_by(email=user.email).first():
        return jsonify({"status": 409,
                        "message": "User already exists"}), 409

    db.session.add(user)
    db.session.commit()

    return jsonify({"status": 201,
                    "message": "User created successfully",
                    data: {
                        "token":"",
                        "user": user_schema.dump(user)
                    }}), 201