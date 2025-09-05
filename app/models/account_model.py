from app.extensions import db
from app.utils.guid_utils import GUID
import uuid

class Account(db.Model):
    id = db.Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(GUID(), db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='accounts')
    balance = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    currency_code = db.Column(db.String(3), nullable=False)
    account_holder = db.Column(db.String(180), nullable=False)
    account_number = db.Column(db.String(30), nullable=False)
    routing_number = db.Column(db.String(80), nullable=True)
    bank_name = db.Column(db.String(255), nullable=False)
    accountType = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    virtual_cards = db.relationship('Virtual_Cards', back_populates='account', cascade="all, delete-orphan")
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())
