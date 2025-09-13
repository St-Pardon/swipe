from app.extensions import db
from app.utils.guid_utils import GUID
import uuid
from datetime import datetime

class Payout(db.Model):
    __tablename__ = 'payouts'
    
    id = db.Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(GUID(), db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='payouts')
    
    # Beneficiary information
    beneficiary_id = db.Column(GUID(), db.ForeignKey('beneficiaries.id'), nullable=True)
    beneficiary = db.relationship('Beneficiaries', back_populates='payouts')
    
    # Source account
    account_id = db.Column(GUID(), db.ForeignKey('account.id'), nullable=False)
    account = db.relationship('Account', back_populates='payouts')
    
    # Stripe payout details
    gateway_payout_id = db.Column(db.String(255), unique=True, nullable=False)
    
    # Payout details
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    
    # Status tracking
    status = db.Column(db.String(50), nullable=False, default='pending')
    # Possible statuses: pending, in_transit, paid, failed, canceled
    
    # Failure information
    failure_code = db.Column(db.String(100), nullable=True)
    failure_message = db.Column(db.Text, nullable=True)
    
    # Destination details
    destination_type = db.Column(db.String(50), nullable=False)  # bank_account, card, etc.
    destination_id = db.Column(db.String(255), nullable=True)  # Stripe destination ID
    
    # Additional information
    description = db.Column(db.Text, nullable=True)
    meta_data = db.Column(db.Text, nullable=True)
    
    # Processing details
    method = db.Column(db.String(50), nullable=False, default='standard')  # standard, instant
    arrival_date = db.Column(db.Date, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())
    processed_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Payout {self.gateway_payout_id}: {self.amount} {self.currency}>'
    
    @classmethod
    def create_bank_payout(cls, user_id, account_id, beneficiary_id, amount, currency, description=None):
        """Create a payout to a bank account"""
        return cls(
            user_id=user_id,
            account_id=account_id,
            beneficiary_id=beneficiary_id,
            amount=amount,
            currency=currency,
            destination_type='bank_account',
            description=description or f'Withdrawal of {amount} {currency} to bank account'
        )
    
    def update_status(self, status, failure_code=None, failure_message=None, arrival_date=None):
        """Update payout status and related fields"""
        self.status = status
        self.updated_at = datetime.utcnow()
        
        if failure_code:
            self.failure_code = failure_code
        
        if failure_message:
            self.failure_message = failure_message
        
        if arrival_date:
            self.arrival_date = arrival_date
        
        if status in ['paid', 'failed', 'canceled']:
            self.processed_at = datetime.utcnow()
    
    def is_successful(self):
        """Check if payout was successful"""
        return self.status == 'paid'
    
    def is_pending(self):
        """Check if payout is still pending"""
        return self.status in ['pending', 'in_transit']
    
    def is_failed(self):
        """Check if payout failed"""
        return self.status in ['failed', 'canceled']
    
    def get_estimated_arrival(self):
        """Get estimated arrival date for the payout"""
        if self.arrival_date:
            return self.arrival_date
        
        # Default estimation based on method and currency
        if self.method == 'instant':
            return datetime.utcnow().date()
        else:
            # Standard payouts typically take 1-3 business days
            from datetime import timedelta
            return (datetime.utcnow() + timedelta(days=2)).date()
