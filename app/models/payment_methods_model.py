from extensions import db
from utils.guid_utils import GUID

class PaymentMethod(db.Model):
    id = db.Column(GUID(), primary_key=True)
    user_id = db.Column(GUID(), db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('payment_methods', lazy=True))
    type = db.Column(db.String(50), nullable=False) # e.g., 'card', 'bank_account', 'mobile_money'
    provider = db.Column(db.String(50), nullable=True) # e.g., 'Visa', 'Mastercard', 'M-Pesa'
    external_id = db.Column(db.String(255), nullable=True) # ID from external payment gateway
    details = db.Column(db.JSON, nullable=True) # Store masked card numbers, bank details, etc.
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)