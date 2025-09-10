from functools import wraps
from flask import Flask, jsonify
from flask_jwt_extended import get_jwt, jwt_required

def role_required(role):
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorator(*args, **kwargs):
            claims = get_jwt()
            if claims["role"] != role:
                return jsonify({"status": 403, "message": "Insufficient permissions"}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper
