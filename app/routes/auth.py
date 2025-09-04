from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt, jwt_required
from app.models.user_model import User
from app.extensions import db, BLOCKLIST
from app.schema.user_schema import User_schema

user_schema = User_schema(session=db.session)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/register", methods=["POST"])
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

    access_token = create_access_token(identity=str(user.id))

    return jsonify({"status": 201,
                    "message": "User created successfully",
                    "data": {
                        "token":access_token,
                        "user": user_schema.dump(user)
                    }}), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get("email")).first()

    if not user or not user.check_password(data.get("password")):
        return jsonify({"status": 401,
                        "message": "Invalid credentials"}), 401

    access_token = create_access_token(identity=str(user.id))

    return jsonify({"status": 200,
                    "message": "Login successful",
                    "data": {
                        "token":access_token,
                        "user": user_schema.dump(user)
                    }})

@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    BLOCKLIST.add(jti)
    return jsonify({"status": 200, "message": "Successfully logged out"}), 200
