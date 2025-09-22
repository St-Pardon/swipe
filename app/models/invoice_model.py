from app.extensions import db
from app.utils.guid_utils import GUID
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
from enum import Enum

class InvoiceStatus(Enum):
    DRAFT = "draft"
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class Invoice(db.Model):
    __tablename__ = 'invoice'
    
    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(GUID(), db.ForeignKey('user.id'), nullable=False)
    
    # Invoice details
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    
    # Financial details
    amount = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='USD')
    tax_amount = db.Column(db.Numeric(precision=10, scale=2), default=0)
    discount_amount = db.Column(db.Numeric(precision=10, scale=2), default=0)
    total_amount = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    
    # Status and dates (store as plain string to avoid Enum mapping issues)
    status = db.Column(db.String(20), nullable=False, default=InvoiceStatus.DRAFT.value)
    issue_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    paid_date = db.Column(db.DateTime)
    
    # Client information
    client_name = db.Column(db.String(255), nullable=False)
    client_email = db.Column(db.String(255), nullable=False)
    client_address = db.Column(db.Text)
    
    # Payment information
    payment_status = db.Column(db.String(50), default='unpaid')
    payment_session_id = db.Column(db.String(255))
    payment_link = db.Column(db.String(500))
    
    # Metadata
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='invoices')
    payment_intents = db.relationship('PaymentIntent', back_populates='invoice', cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        super(Invoice, self).__init__(**kwargs)
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        if not self.due_date and self.issue_date:
            self.due_date = self.issue_date + timedelta(days=30)  # Default 30 days
        self.calculate_total()
    
    def generate_invoice_number(self):
        """Generate unique invoice number"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"INV-{timestamp}-{str(uuid.uuid4())[:8].upper()}"
    
    def calculate_total(self):
        """Calculate total amount including tax and discount"""
        if self.amount is not None:
            base_amount = Decimal(str(self.amount))
            tax = Decimal(str(self.tax_amount or 0))
            discount = Decimal(str(self.discount_amount or 0))
            self.total_amount = base_amount + tax - discount
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue"""
        if self.status in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED]:
            return False
        return datetime.utcnow() > self.due_date
    
    @property
    def is_due_soon(self):
        """Check if invoice is due within 7 days"""
        if self.status in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED]:
            return False
        days_until_due = (self.due_date - datetime.utcnow()).days
        return 0 <= days_until_due <= 7
    
    def update_status(self):
        """Update status based on current conditions"""
        if self.status == InvoiceStatus.DRAFT.value:
            return  # Don't auto-update draft status
        
        if self.payment_status == 'paid':
            self.status = InvoiceStatus.PAID.value
            if not self.paid_date:
                self.paid_date = datetime.utcnow()
        elif self.is_overdue and self.status != InvoiceStatus.PAID.value:
            self.status = InvoiceStatus.OVERDUE.value
        elif self.status == InvoiceStatus.DRAFT.value:
            self.status = InvoiceStatus.PENDING.value
    
    def set_status_from_string(self, status_str):
        """Set status from string value"""
        status_mapping = {e.value: e.value for e in InvoiceStatus}
        if status_str and status_str.lower() in status_mapping:
            self.status = status_mapping[status_str.lower()]
    
    @classmethod
    def create_invoice(cls, user_id, title, client_name, client_email, amount, currency='USD', **kwargs):
        """Create a new invoice"""
        invoice = cls(
            user_id=user_id,
            title=title,
            client_name=client_name,
            client_email=client_email,
            amount=amount,
            currency=currency,
            **kwargs
        )
        return invoice
    
    def to_dict(self):
        """Convert invoice to dictionary"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'invoice_number': self.invoice_number,
            'title': self.title,
            'description': self.description,
            'amount': str(self.amount),
            'currency': self.currency,
            'tax_amount': str(self.tax_amount or 0),
            'discount_amount': str(self.discount_amount or 0),
            'total_amount': str(self.total_amount),
            'status': self.status,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'paid_date': self.paid_date.isoformat() if self.paid_date else None,
            'client_name': self.client_name,
            'client_email': self.client_email,
            'client_address': self.client_address,
            'payment_status': self.payment_status,
            'payment_link': self.payment_link,
            'notes': self.notes,
            'is_overdue': self.is_overdue,
            'is_due_soon': self.is_due_soon,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
