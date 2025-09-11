from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import or_
from app.extensions import db

from app.models.transactions_model import Transaction
from app.schema.transactions_schema import TransactionSchema


transaction_bp = Blueprint("transaction", __name__)


def create_transaction():
    pass

@transaction_bp("/transactions", method="GET")
@jwt_required()
def get_transactions():
    """Get all transactions for the authenticated user with filtering, pagination and sorting"""
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters for filtering, pagination and sorting
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)
        transaction_type = request.args.get('transaction_type')
        transaction_status = request.args.get('transaction_status')
        search = request.args.get('search', default='', type=str)
        
        query = Transaction.query.filter_by(user_id=user_id)

        if search:
            query = query.filter(or_(
                Transaction.description.ilike(f'%{search}%'),
                Transaction.amount.ilike(f'%{search}%'),
                Transaction.fee.ilike(f'%{search}%'),
                Transaction.type.ilike(f'%{search}%'),
                Transaction.status.ilike(f'%{search}%')
            ))

        # add type and status
        if transaction_type:
            query = query.filter(Transaction.type == transaction_type)
        if transaction_status:
            query = query.filter(Transaction.status == transaction_status)

        # Apply pagination
        transactions = query.paginate(page=page, per_page=size, error_out=False)

        transaction_schema = TransactionSchema(many=True)
        result = transaction_schema.dump(transactions.items)

        return jsonify({
            "status": 200,
            "message": "Transactions retrieved successfully",
            "data": result
        }), 200

    except Exception as e:
        return jsonify({
            "status": 500,
            "message": "An error occurred while retrieving the transactions",
            "error": str(e)
        }), 500

@transaction_bp("/transaction/<string:id>", method="GET")
@jwt_required()
def get_transaction(id):
    """Get a specific transaction by ID"""
    try:
        user_id = get_jwt_identity()
        transaction = Transaction.query.filter_by(id=id, user_id=user_id).first()

        if not transaction:
            return jsonify({
                "status": 404,
                "message": "Transaction not found"
            }), 404

        transaction_schema = TransactionSchema()
        result = transaction_schema.dump(transaction)

        return jsonify({
            "status": 200,
            "message": "Transaction retrieved successfully",
            "data": result
        }), 200

    except Exception as e:
        return jsonify({
            "status": 500,
            "message": "An error occurred while retrieving the transaction",
            "error": str(e)
        }), 500

@transaction_bp("/transaction/<string:id>", method="DELETE")
@jwt_required()
def delete_transaction(id):
    """Delete a specific transaction by ID"""
    try:
        user_id = get_jwt_identity()
        transaction = Transaction.query.filter_by(id=id, user_id=user_id).first()

        if not transaction:
            return jsonify({
                "status": 404,
                "message": "Transaction not found"
            }), 404

        db.session.delete(transaction)
        db.session.commit()

        return jsonify({
            "status": 200,
            "message": "Transaction deleted successfully"
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": 500,
            "message": "An error occurred while deleting the transaction",
            "error": str(e)
        }), 500
