from extensions import db
from utils.guid_utils import GUID

class Beneficiaries(db.Model):
    id = db.Column(GUID(), primary_key=True)
    user_id = db.Column(GUID(), db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('beneficiaries', lazy=True))
    account_id = db.Column(GUID(), db.ForeignKey('account.id'), nullable=False)
    account = db.relationship('Account', backref=db.backref('beneficiaries', lazy=True))
    bank_name = db.Column(db.String(255), nullable=False)
    account_number = db.Column(db.String(255), nullable=False)
    routing_number = db.Column(db.String(255), nullable=False)
    beneficiary_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    transaction = db.relationship('Transaction', backref=db.backref('beneficiaries', lazy=True))
