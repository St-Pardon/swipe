from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field
from marshmallow import fields, validates, ValidationError, validate
from app.models.virtual_cards_model import VirtualCard
from app.schema.user_schema import User_schema
from app.schema.account_schema import AccountSchema
from app.extensions import db

class VirtualCardSchema(SQLAlchemySchema):
    class Meta:
        model = VirtualCard
        load_instance = True
        sqla_session = db.session
        
    id = auto_field(dump_only=True)
    user_id = auto_field(load_only=True, required=False)
    account_id = auto_field(load_only=True, required=True)
    card_kind = fields.String(required=True, validate=validate.OneOf(['virtual', 'physical']))
    card_type = fields.String(required=True, validate=validate.OneOf(['debit', 'credit']))
    card_holder = auto_field(required=False, dump_only=True)  # Set from user's name
    card_number = fields.Method("get_masked_card_number", dump_only=True)
    expiration_date = auto_field(dump_only=True)
    cvv = fields.String(dump_only=True)
    pin = fields.String(load_only=True, required=False, validate=validate.Length(min=4, max=6))
    spending_limit = auto_field(validate=validate.Range(min=0))
    is_default = auto_field(load_default=False)
    is_active = auto_field()
    created_at = auto_field(dump_only=True)
    user = fields.Nested(User_schema(only=("id", "name", "email")), dump_only=True)
    account = fields.Nested(AccountSchema(only=("id", "account_number", "bank_name")), dump_only=True)
    # Optional Stripe payment method id supplied by client when they have already created it client-side
    stripe_payment_method_id = fields.String(load_only=True, required=False, validate=validate.Regexp(r'^pm_'))
    
    def get_masked_card_number(self, obj):
        """Return a masked version of the card number for display."""
        if obj.card_number:
            return f"{obj.card_number[:4]} **** **** {obj.card_number[-4:]}"
        return None
    
    @validates('spending_limit')
    def validate_spending_limit(self, value, **kwargs):
        """Validate that spending limit is a non-negative number"""
        if value < 0:
            raise ValidationError("Spending limit must be a non-negative number")
    
    @validates('card_holder')
    def validate_card_holder(self, value, **kwargs):
        """Validate card holder name contains only allowed characters"""
        if not all(char.isalpha() or char.isspace() or char in ['-', "'"] for char in value):
            raise ValidationError("Card holder name can only contain letters, spaces, hyphens, and apostrophes")