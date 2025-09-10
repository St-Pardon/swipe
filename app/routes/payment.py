from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import or_
from app.models.payment_methods_model import PaymentMethod

from app.extensions import db
from app.schema.payment_methods_schema import PaymentMethodScema

payment_bp = Blueprint("payment", __name__)

@payment_bp.route("/method", methods=["POST"])
@jwt_required
def create_payment_method():
    """Create a new payment method for the authenticated user."""
    try:
        data = request.get_json()
        user_id = get_jwt_identity()

        payment_method_schema = PaymentMethodScema()
        errors = payment_method_schema.validate(data)
        if errors:
            return jsonify({"status": 400, "message": "Invalid data", "errors": errors}), 400

        # Ensure user_id from JWT is used
        data['user_id'] = user_id

        if data.get('is_default'):
            PaymentMethod.query.filter_by(user_id=user_id, is_default=True).update({'is_default': False})
        
        payment_method = payment_method_schema.load(data)

        db.session.add(payment_method)
        db.session.commit()

        result = payment_method_schema.dump(payment_method)

        return jsonify({
            "status": 201,
            "message": "Payment method created successfully",
            "data": result
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": 500, "message": str(e)}), 500


@payment_bp.route("/methods", methods=["GET"])
@jwt_required()
def get_payment_methods():
    """Retrieve all payment methods for the authenticated user with filtering, pagination and sorting."""
    try:
        user_id = get_jwt_identity()

        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)
        search = request.args.get('search', default='', type=str)
        method_type = request.args.get('type')
        provider = request.args.get('provider')

        if page < 1:
            page = 1
        if size < 1 or size > 100:
            size = 10

        query = PaymentMethod.query.filter_by(user_id=user_id)

        if method_type:
            query = query.filter(PaymentMethod.type == method_type)
        if provider:
            query = query.filter(PaymentMethod.provider == provider)
        if search:
            query = query.filter(or_(
                PaymentMethod.type.ilike(f'%{search}%'),
                PaymentMethod.provider.ilike(f'%{search}%')
            ))

        payment_methods = query.paginate(page=page, per_page=size, error_out=False)

        payment_method_schema = PaymentMethodScema(many=True)
        result = payment_method_schema.dump(payment_methods.items)

        return jsonify({
            "status": 200,
            "message": "Payment methods retrieved successfully",
            "data": result,
            "pagination": {
                "page": page,
                "size": size,
                "total": payment_methods.total,
                "pages": payment_methods.pages
            }
        }), 200

    except Exception as e:
        return jsonify({"status": 500, "message": str(e)}), 500


@payment_bp.route("/method/<string:method_id>", methods=["GET"])
@jwt_required()
def get_payment_method(method_id):
    """Retrieve a specific payment method by ID for the authenticated user."""
    try:
        user_id = get_jwt_identity()

        payment_method = PaymentMethod.query.filter_by(id=method_id, user_id=user_id).first()

        if not payment_method:
            return jsonify({"status": 404, "message": "Payment method not found"}), 404

        payment_method_schema = PaymentMethodScema()
        result = payment_method_schema.dump(payment_method)

        return jsonify({
            "status": 200,
            "message": "Payment method retrieved successfully",
            "data": result
        }), 200

    except Exception as e:
        return jsonify({"status": 500, "message": str(e)}), 500


@payment_bp.route("/method/<string:method_id>", methods=["DELETE"])
@jwt_required()
def delete_payment_method(method_id):
    """Delete a specific payment method by ID for the authenticated user."""
    try:
        user_id = get_jwt_identity()
        payment_method = PaymentMethod.query.filter_by(id=method_id, user_id=user_id).first()

        if not payment_method:
            return jsonify({"status": 404, "message": "Payment method not found"}), 404

        db.session.delete(payment_method)
        db.session.commit()

        return jsonify({"status": 200, "message": "Payment method deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": 500, "message": str(e)}), 500
