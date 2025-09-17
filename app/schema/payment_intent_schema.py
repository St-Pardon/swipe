from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field
from marshmallow import fields, validates, ValidationError, validate
from app.models.payment_intent_model import PaymentIntent
from app.extensions import db

class PaymentIntentSchema(SQLAlchemySchema):
    class Meta:
        model = PaymentIntent
        load_instance = True
        sqla_session = db.session

    id = auto_field(dump_only=True)
    user_id = auto_field(load_only=True, required=False)
    account_id = auto_field(load_only=True, required=False)
    virtual_card_id = auto_field(load_only=True, required=False)
    amount = auto_field(required=True)
    currency = auto_field(required=True, validate=validate.Length(min=3, max=3))
    status = auto_field(dump_only=True)
    intent_type = auto_field(required=True)
    description = auto_field()
    gateway_intent_id = auto_field(dump_only=True)
    client_secret = auto_field(dump_only=True, load_only=True)  # Don't expose in nested objects
    payment_method_id = auto_field(dump_only=True)
    payment_method_type = auto_field(dump_only=True)
    meta_data = auto_field(dump_only=True)
    created_at = auto_field(dump_only=True)
    updated_at = auto_field(dump_only=True)

    # Nested relationships
    account = fields.Nested("AccountSchema", only=("id", "account_number_masked", "currency"), dump_only=True)
    virtual_card = fields.Nested("VirtualCardSchema", only=("id", "card_number", "card_type"), dump_only=True)

    @validates('intent_type')
    def validate_intent_type(self, value, **kwargs):
        """Validate intent type"""
        valid_types = ['wallet_funding', 'card_funding', 'invoice_payment', 'card_topup']
        if value not in valid_types:
            raise ValidationError(f"Invalid intent type. Must be one of: {', '.join(valid_types)}")

    @validates('currency')
    def validate_currency(self, value, **kwargs):
        """Validate currency code"""
        valid_currencies = ['USD', 'EUR', 'GBP', 'NGN', 'JPY', 'CAD', 'AUD']
        if value.upper() not in valid_currencies:
            raise ValidationError(f"Invalid currency. Must be one of: {', '.join(valid_currencies)}")

    @validates('amount')
    def validate_amount(self, value, **kwargs):
        """Validate amount is positive"""
        if value <= 0:
            raise ValidationError("Amount must be positive")
