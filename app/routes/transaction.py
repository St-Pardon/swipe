from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import or_, cast
from sqlalchemy.sql import text
from sqlalchemy.types import String
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

        page = request.args.get("page", default=1, type=int)
        size = request.args.get("size", default=10, type=int)
        page = 1 if page < 1 else page
        size = 10 if size < 1 else size

        transaction_type = request.args.get("type") or request.args.get("transaction_type")
        transaction_status = request.args.get("status") or request.args.get("transaction_status")
        search = request.args.get("search", default="", type=str).strip()
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        sort_by = request.args.get("sort_by", default="created_at")
        sort_order = request.args.get("sort_order", default="desc").lower()

        query = Transaction.query.filter_by(user_id=user_id)

        if transaction_type:
            query = query.filter(Transaction.type == transaction_type)

        if transaction_status:
            query = query.filter(Transaction.status == transaction_status)

        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str)
                query = query.filter(Transaction.created_at >= start_date)
            except ValueError:
                return jsonify({
                    "status": 400,
                    "message": "Invalid start_date. Use ISO 8601 format (e.g. 2025-09-30T21:34:48)."
                }), 400

        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str)
                query = query.filter(Transaction.created_at <= end_date)
            except ValueError:
                return jsonify({
                    "status": 400,
                    "message": "Invalid end_date. Use ISO 8601 format (e.g. 2025-09-30T21:34:48)."
                }), 400

        if search:
            like_value = f"%{search}%"
            query = query.filter(or_(
                Transaction.description.ilike(like_value),
                Transaction.type.ilike(like_value),
                Transaction.status.ilike(like_value),
                cast(Transaction.currency_code, String).ilike(like_value),
                cast(Transaction.amount, String).ilike(like_value),
                cast(Transaction.fee, String).ilike(like_value)
            ))

        if sort_by not in {"created_at", "amount", "status", "type"}:
            sort_by = "created_at"

        sort_column = getattr(Transaction, sort_by)
        sort_column = sort_column.desc() if sort_order != "asc" else sort_column.asc()
        query = query.order_by(sort_column)

        transactions = query.paginate(page=page, per_page=size, error_out=False)

        schema = TransactionSchema(many=True)
        data = schema.dump(transactions.items)

        return jsonify({
            "status": 200,
            "message": "Transactions retrieved successfully",
            "data": data,
            "pagination": {
                "page": page,
                "size": size,
                "total": transactions.total,
                "pages": transactions.pages,
                "has_next": transactions.has_next,
                "has_prev": transactions.has_prev,
            }
        }), 200

    except Exception as e:
        db.session.rollback()
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
