from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.guid_utils import GUID
import uuid
from app.models.virtual_cards_model import VirtualCard


class User(db.Model):
    id = db.Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    accountType = db.Column(db.String(120), nullable=False, default='freelancer')
    country = db.Column(db.String(120), nullable=True)
    countryCode = db.Column(db.String(120), nullable=True)
    city = db.Column(db.String(120), nullable=True)
    role = db.Column(db.String(120), nullable=False, default='user')
    address = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    accounts = db.relationship('Account', back_populates='user', cascade="all, delete-orphan")
    virtual_cards = db.relationship('VirtualCard', back_populates='user', cascade="all, delete-orphan")
    transactions = db.relationship('Transaction', back_populates='user', cascade="all, delete-orphan")
    beneficiaries = db.relationship('Beneficiaries', back_populates='user', cascade="all, delete-orphan")
    payment_intents = db.relationship('PaymentIntent', back_populates='user', cascade="all, delete-orphan")
    payouts = db.relationship('Payout', back_populates='user', cascade="all, delete-orphan")
    # payment_methods = db.relationship('PaymentMethod', back_populates='user', cascade="all, delete-orphan")  # Removed
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
