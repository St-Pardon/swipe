from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field
from marshmallow import fields, validates, ValidationError, validate
from app.models.account_model import Account
from app.schema.user_schema import User_schema
from app.extensions import db

# Define valid currency codes at the module level for reusability
VALID_CURRENCY_CODES = ['NGN', 'USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY', 'INR']

class AccountSchema(SQLAlchemySchema):
    class Meta:
        model = Account
        load_instance = True
        sqla_session = db.session

    id = auto_field(dump_only=True)
    user_id = auto_field(load_only=True, required=False)
    balance = auto_field(dump_only=True)
    currency = auto_field(required=True, validate=validate.Length(min=3, max=3))
    currency_code = auto_field(required=True, validate=validate.Length(min=3, max=3))
    account_holder = auto_field(required=True, validate=validate.Length(min=1, max=180))
    account_number = fields.Method("get_full_account_number", dump_only=True)
    routing_number = auto_field(validate=validate.Length(max=80))
    bank_name = auto_field(required=True, validate=validate.Length(min=1, max=255))
    accountType = auto_field(required=True, validate=validate.Length(min=1, max=50))
    address = auto_field(validate=validate.Length(max=255))
    is_default = auto_field(load_default=False)
    created_at = auto_field(dump_only=True)
    updated_at = auto_field(dump_only=True)

    user = fields.Nested("User_schema", only=("id", "name", "email"), dump_only=True)
    
    # Custom field for the masked account number (for display)
    account_number_masked = fields.Method("get_masked_account_number", dump_only=True)

    def get_full_account_number(self, obj):
        """Return the decrypted account number."""
        if hasattr(obj, 'get_account_number'):
            return obj.get_account_number()
        return None
    
    def get_masked_account_number(self, obj):
        """Return a masked version of the account number for display"""
        if hasattr(obj, 'get_account_number'):
            full_account = obj.get_account_number()
            return f"****{full_account[-4:]}" if full_account else None
        return None
    
    @validates('currency_code')
    def validate_currency_code(self, value, **kwargs):
        """Validate that currency code is a valid ISO code"""
        if value not in VALID_CURRENCY_CODES:
            raise ValidationError(f"Invalid currency code. Must be one of: {', '.join(VALID_CURRENCY_CODES)}")
    
    @validates('accountType')
    def validate_account_type(self, value, **kwargs):
        """Validate account type"""
        valid_types = ['checking', 'savings', 'business', 'investment', 'loan', 'credit']
        if value.lower() not in valid_types:
            raise ValidationError(f"Invalid account type. Must be one of: {', '.join(valid_types)}")