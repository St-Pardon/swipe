from extensions import db
from utils.guid_utils import GUID

class Transaction(db.Model):
    id = db.Column(GUID(), primary_key=True)
    user_id = db.Column(GUID(), db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('transactions', lazy=True))
    debit_account_id = db.Column(GUID(), db.ForeignKey('account.id'), nullable=False)
    credit_account_id = db.Column(GUID(), db.ForeignKey('account.id'), nullable=False)
    account = db.relationship('Account', backref=db.backref('transactions', lazy=True))
    payment_method_id = db.Column(GUID(), db.ForeignKey('payment_method.id'), nullable=False)
    # payment_method = db.relationship('PaymentMethod', backref=db.backref('transactions', lazy=True))
    beneficiary_id = db.Column(GUID(), db.ForeignKey('beneficiary.id'), nullable=False)
    invoice_id = db.Column(GUID(), db.ForeignKey('invoice.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    fee = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    currency_code = db.Column(db.String(3), nullable=False)
    metadata = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, nullable=False)


class transactionView(db.Model):
    id = db.Column(GUID(), primary_key=True)
    transaction_id = db.Column(GUID(), db.ForeignKey('transaction.id'), nullable=False)
    account_id = db.Column(GUID(), db.ForeignKey('account.id'), nullable=False)
    view_type = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)