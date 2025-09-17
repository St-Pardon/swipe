from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import or_
from datetime import datetime
from app.extensions import db

from app.models.transactions_model import Transaction, TransactionView
from app.schema.transactions_schema import TransactionSchema


transaction_bp = Blueprint("transaction", __name__)


def create_transaction(
    *,
    user_id,
    txn_type,
    status,
    amount,
    currency_code,
    description=None,
    debit_account_id=None,
    credit_account_id=None,
    payment_method_id=None,
    beneficiary_id=None,
    metadata=None,
):
    """
    Create a Transaction row and associated TransactionView rows for quick listing.

    Required params:
      - user_id: UUID of the owner
      - txn_type: e.g. 'wallet_fund_intent', 'wallet_fund', 'payout', 'transfer', 'card_wallet_fund_intent'
      - status: 'pending' | 'succeeded' | 'failed' | 'canceled'
      - amount: float or Decimal (will be stored as float)
      - currency_code: 'USD', 'EUR', etc.

    Optional params help contextualize the transaction for UI and auditing.
    """
    created_at = datetime.utcnow()
    txn = Transaction(
        user_id=user_id,
        debit_account_id=debit_account_id,
        credit_account_id=credit_account_id,
        payment_method_id=payment_method_id,
        beneficiary_id=beneficiary_id,
        type=txn_type,
        status=status,
        amount=float(amount),
        fee=0.0,
        description=description,
        currency_code=currency_code,
        transction_metadata=metadata or {},
        created_at=created_at,
    )
    db.session.add(txn)
    db.session.flush()  # get txn.id

    # Create views for involved accounts to support per-account listings
    if debit_account_id:
        db.session.add(
            TransactionView(
                transaction_id=txn.id,
                account_id=debit_account_id,
                view_type="debit",
                created_at=created_at,
            )
        )
    if credit_account_id:
        db.session.add(
            TransactionView(
                transaction_id=txn.id,
                account_id=credit_account_id,
                view_type="credit",
                created_at=created_at,
            )
        )

    # Caller is responsible for committing
    return txn

@transaction_bp.route("/transactions", methods=["GET"])
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

@transaction_bp.route("/transaction/<string:id>", methods=["GET"])
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

@transaction_bp.route("/transaction/<string:id>", methods=["DELETE"])
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
