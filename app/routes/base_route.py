from flask import Blueprint

base_bp = Blueprint('base', __name__)

@base_bp.route("/", methods=["GET"])
def home():
    return {"message": "Hello"}, 200
