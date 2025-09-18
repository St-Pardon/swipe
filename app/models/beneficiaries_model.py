from app.extensions import db
from app.utils.guid_utils import GUID
from datetime import datetime
import uuid

class Beneficiaries(db.Model):
    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(GUID(), db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='beneficiaries')
    account_id = db.Column(GUID(), db.ForeignKey('account.id'), nullable=False)
    account = db.relationship('Account', backref=db.backref('beneficiaries', cascade='all, delete-orphan'))
    bank_name = db.Column(db.String(255), nullable=False)
    account_number = db.Column(db.String(255), nullable=False)
    routing_number = db.Column(db.String(255), nullable=False)
    beneficiary_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    transactions = db.relationship('Transaction', back_populates='beneficiary')
    payouts = db.relationship('Payout', back_populates='beneficiary', cascade="all, delete-orphan")
    
    @classmethod
    def create_beneficiary(cls, user_id, account_id, bank_name, account_number, routing_number, beneficiary_name):
        """Create a new beneficiary"""
        return cls(
            user_id=user_id,
            account_id=account_id,
            bank_name=bank_name,
            account_number=account_number,
            routing_number=routing_number,
            beneficiary_name=beneficiary_name
        )
