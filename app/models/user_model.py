from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.guid_utils import GUID
import uuid
import secrets
from sqlalchemy.orm import relationship
from app.models.virtual_cards_model import VirtualCard


class User(db.Model):
    __tablename__ = 'user'
    
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
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    email_verification_token = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    accounts = db.relationship('Account', back_populates='user', cascade="all, delete-orphan")
    virtual_cards = db.relationship('VirtualCard', back_populates='user', cascade="all, delete-orphan")
    transactions = relationship('Transaction', back_populates='user', cascade="all, delete-orphan")
    beneficiaries = db.relationship('Beneficiaries', back_populates='user', cascade="all, delete-orphan")
    payment_intents = db.relationship('PaymentIntent', back_populates='user', cascade="all, delete-orphan")
    payouts = db.relationship('Payout', back_populates='user', cascade="all, delete-orphan")
    # payment_methods = db.relationship('PaymentMethod', back_populates='user', cascade="all, delete-orphan")  # Removed
    two_factor_auth = db.relationship('TwoFactorAuth', back_populates='user', uselist=False, cascade="all, delete-orphan")
    invoices = db.relationship('Invoice', back_populates='user', cascade="all, delete-orphan")
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def generate_email_verification_token(self):
        """Generate a secure token for email verification"""
        self.email_verification_token = secrets.token_urlsafe(32)
        return self.email_verification_token

    def verify_email_token(self, token):
        """Verify email verification token"""
        return self.email_verification_token == token

    def mark_email_verified(self):
        """Mark user's email as verified"""
        self.email_verified = True
        self.email_verification_token = None  # Clear the token after verification
