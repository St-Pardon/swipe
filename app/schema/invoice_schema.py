from marshmallow import Schema, fields, validate, validates, ValidationError, post_load
from datetime import datetime, timedelta
from decimal import Decimal

class InvoiceCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str(allow_none=True, validate=validate.Length(max=1000))
    
    # Financial fields
    amount = fields.Decimal(required=True, validate=validate.Range(min=0.01), places=2)
    currency = fields.Str(load_default='USD', validate=validate.Length(equal=3))
    tax_amount = fields.Decimal(load_default=0, validate=validate.Range(min=0), places=2)
    discount_amount = fields.Decimal(load_default=0, validate=validate.Range(min=0), places=2)
    
    # Client information
    client_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    client_email = fields.Email(required=True)
    client_address = fields.Str(allow_none=True, validate=validate.Length(max=500))
    
    # Dates
    issue_date = fields.DateTime(allow_none=True, format='iso')
    due_date = fields.DateTime(allow_none=True, format='iso')
    
    # Optional fields
    notes = fields.Str(allow_none=True, validate=validate.Length(max=1000))
    status = fields.Str(load_default='draft', validate=validate.OneOf(['draft', 'pending']))
    
    @validates('due_date')
    def validate_due_date(self, value):
        if value and value <= datetime.utcnow():
            raise ValidationError('Due date must be in the future')
    
    @post_load
    def process_data(self, data, **kwargs):
        # Set default dates if not provided
        if not data.get('issue_date'):
            data['issue_date'] = datetime.utcnow()
        
        if not data.get('due_date'):
            issue_date = data.get('issue_date', datetime.utcnow())
            data['due_date'] = issue_date + timedelta(days=30)
        
        return data

class InvoiceUpdateSchema(Schema):
    title = fields.Str(validate=validate.Length(min=1, max=255))
    description = fields.Str(validate=validate.Length(max=1000))
    
    # Financial fields
    amount = fields.Decimal(validate=validate.Range(min=0.01), places=2)
    currency = fields.Str(validate=validate.Length(equal=3))
    tax_amount = fields.Decimal(validate=validate.Range(min=0), places=2)
    discount_amount = fields.Decimal(validate=validate.Range(min=0), places=2)
    
    # Client information
    client_name = fields.Str(validate=validate.Length(min=1, max=255))
    client_email = fields.Email()
    client_address = fields.Str(validate=validate.Length(max=500))
    
    # Dates
    issue_date = fields.DateTime(format='iso')
    due_date = fields.DateTime(format='iso')
    
    # Status and notes
    notes = fields.Str(validate=validate.Length(max=1000))
    status = fields.Str(validate=validate.OneOf(['draft', 'pending', 'paid', 'overdue', 'cancelled']))
    
    @validates('due_date')
    def validate_due_date(self, value):
        if value and value <= datetime.utcnow():
            raise ValidationError('Due date must be in the future')

class InvoiceResponseSchema(Schema):
    id = fields.Str()
    user_id = fields.Str()
    invoice_number = fields.Str()
    title = fields.Str()
    description = fields.Str()
    
    # Financial fields
    amount = fields.Str()
    currency = fields.Str()
    tax_amount = fields.Str()
    discount_amount = fields.Str()
    total_amount = fields.Str()
    
    # Status and dates
    status = fields.Method("get_status")
    issue_date = fields.DateTime(format='iso')
    due_date = fields.DateTime(format='iso')
    paid_date = fields.DateTime(format='iso')
    
    # Client information
    client_name = fields.Str()
    client_email = fields.Str()
    client_address = fields.Str()
    
    # Payment information
    payment_status = fields.Str()
    payment_link = fields.Str()
    
    # Metadata
    notes = fields.Str()
    is_overdue = fields.Bool()
    is_due_soon = fields.Bool()
    created_at = fields.DateTime(format='iso')
    updated_at = fields.DateTime(format='iso')
    
    def get_status(self, obj):
        """Convert enum status to string"""
        if hasattr(obj.status, 'value'):
            return obj.status.value
        return str(obj.status).replace('InvoiceStatus.', '').lower()

class InvoiceFilterSchema(Schema):
    # Pagination
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    size = fields.Int(load_default=10, validate=validate.Range(min=1, max=100))
    
    # Search
    search = fields.Str(load_default='')
    
    # Filters
    status = fields.Str(validate=validate.OneOf(['draft', 'pending', 'paid', 'overdue', 'cancelled']))
    client_name = fields.Str()
    client_email = fields.Str()
    currency = fields.Str(validate=validate.Length(equal=3))
    
    # Date filters
    issue_date_from = fields.DateTime(format='iso')
    issue_date_to = fields.DateTime(format='iso')
    due_date_from = fields.DateTime(format='iso')
    due_date_to = fields.DateTime(format='iso')
    
    # Amount filters
    amount_min = fields.Decimal(validate=validate.Range(min=0), places=2)
    amount_max = fields.Decimal(validate=validate.Range(min=0), places=2)
    
    # Sorting
    sort_by = fields.Str(load_default='created_at', validate=validate.OneOf([
        'created_at', 'updated_at', 'issue_date', 'due_date', 'amount', 'total_amount', 'status'
    ]))
    sort_order = fields.Str(load_default='desc', validate=validate.OneOf(['asc', 'desc']))
    
    # Special filters
    overdue_only = fields.Bool(load_default=False)
    due_soon_only = fields.Bool(load_default=False)
    unpaid_only = fields.Bool(load_default=False)
