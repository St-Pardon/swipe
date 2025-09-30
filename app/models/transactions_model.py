import uuid

from app.extensions import db
from app.utils.guid_utils import GUID

class Transaction(db.Model):
    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(GUID(), db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='transactions')
    debit_account_id = db.Column(GUID(), db.ForeignKey('account.id'), nullable=True)
    credit_account_id = db.Column(GUID(), db.ForeignKey('account.id'), nullable=True)
    debit_account = db.relationship('Account', foreign_keys=[debit_account_id], back_populates='debit_transactions')
    credit_account = db.relationship('Account', foreign_keys=[credit_account_id], back_populates="credit_transactions")
    payment_method_id = db.Column(GUID(), nullable=True)  # Removed PaymentMethod FK
    # payment_method = db.relationship('PaymentMethod', back_populates='transactions')  # Removed
    beneficiary_id = db.Column(GUID(), db.ForeignKey('beneficiaries.id'), nullable=True)
    beneficiary = db.relationship('Beneficiaries', back_populates='transactions')
    # invoice_id = db.Column(GUID(), db.ForeignKey('invoice.id'), nullable=True)
    type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    fee = db.Column(db.Float, nullable=False, default=0.0)
    description = db.Column(db.Text)
    currency_code = db.Column(db.String(3), nullable=False)
    transction_metadata = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, nullable=False)
    view = db.relationship('TransactionView', back_populates='transaction', cascade='all, delete-orphan')




class TransactionView(db.Model):
    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = db.Column(GUID(), db.ForeignKey('transaction.id'), nullable=False)
    transaction = db.relationship('Transaction', back_populates='view')
    account_id = db.Column(GUID(), db.ForeignKey('account.id'), nullable=False)
    account = db.relationship('Account', back_populates='view')
    view_type = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)