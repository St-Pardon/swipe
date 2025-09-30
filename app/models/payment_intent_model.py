from app.extensions import db
from app.utils.guid_utils import GUID
import uuid
from datetime import datetime

class PaymentIntent(db.Model):
    __tablename__ = 'payment_intents'
    
    id = db.Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(GUID(), db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='payment_intents')
    
    # Stripe payment intent details
    gateway_intent_id = db.Column(db.String(255), unique=True, nullable=False)
    client_secret = db.Column(db.String(255), nullable=True)
    
    # Payment details
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    
    # Status tracking
    status = db.Column(db.String(50), nullable=False, default='requires_payment_method')
    # Possible statuses: requires_payment_method, requires_confirmation, requires_action, 
    # processing, requires_capture, canceled, succeeded
    
    # Intent type and metadata
    intent_type = db.Column(db.String(50), nullable=False)
    # Types: wallet_funding, invoice_payment, card_topup
    
    # Related entities
    account_id = db.Column(GUID(), db.ForeignKey('account.id'), nullable=True)
    account = db.relationship('Account', back_populates='payment_intents')
    
    # Virtual card relationship for card payments
    virtual_card_id = db.Column(GUID(), db.ForeignKey('virtual_card.id'), nullable=True)
    virtual_card = db.relationship('VirtualCard', back_populates='payment_intents')
    
    # Invoice relationship for invoice payments
    invoice_id = db.Column(GUID(), db.ForeignKey('invoice.id'), nullable=True)
    invoice = db.relationship('Invoice', back_populates='payment_intents')
    
    # Additional metadata (stored as text for SQLite compatibility)
    meta_data = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    
    # Payment method details (stored from Stripe)
    payment_method_id = db.Column(db.String(255), nullable=True)
    payment_method_type = db.Column(db.String(50), nullable=True)  # card, bank_transfer, etc.
    
    # Timestamps
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())
    confirmed_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<PaymentIntent {self.gateway_intent_id}: {self.amount} {self.currency}>'
    
    @classmethod
    def create_wallet_funding_intent(cls, user_id, account_id, amount, currency, description=None):
        """Create a payment intent for wallet funding"""
        return cls(
            user_id=user_id,
            account_id=account_id,
            amount=amount,
            currency=currency,
            intent_type='wallet_funding',
            description=description or f'Add {amount} {currency} to wallet'
        )
    
    @classmethod
    def create_invoice_payment_intent(cls, user_id, amount, currency, description=None, invoice_id=None, metadata=None):
        """Create a payment intent for invoice payment"""
        intent = cls(
            user_id=user_id,
            amount=amount,
            currency=currency,
            intent_type='invoice_payment',
            description=description or f'Invoice payment of {amount} {currency}'
        )
        if invoice_id:
            intent.invoice_id = invoice_id
        if metadata:
            intent.meta_data = metadata
        return intent
    
    def update_status(self, status, payment_method_id=None, payment_method_type=None):
        """Update payment intent status and related fields"""
        self.status = status
        self.updated_at = datetime.utcnow()
        
        if payment_method_id:
            self.payment_method_id = payment_method_id
        
        if payment_method_type:
            self.payment_method_type = payment_method_type
        
        if status == 'succeeded':
            self.confirmed_at = datetime.utcnow()
    
    def is_successful(self):
        """Check if payment intent was successful"""
        return self.status == 'succeeded'
    
    def is_pending(self):
        """Check if payment intent is still pending"""
        return self.status in ['requires_payment_method', 'requires_confirmation', 'requires_action', 'processing']
    
    def is_failed(self):
        """Check if payment intent failed"""
        return self.status in ['canceled', 'payment_failed']
