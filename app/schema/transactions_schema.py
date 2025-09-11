from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field
from marshmallow import fields, validate
from app.extensions import db
from app.models.transactions_model import Transaction
from app.schema.account_schema import AccountSchema
from app.schema.user_schema import User_schema


class TransactionSchema(SQLAlchemySchema):
    class Meta:
        model = Transaction
        load_instance = True
        sqla_session = db.session

    id = auto_field(dump_only=True)
    user_id = auto_field(load_only=True, required=True)
    debit_account_id = auto_field(load_only=True)
    credit_account_id = auto_field(load_only=True)
    payment_method_id = auto_field(load_only=True)
    beneficiary_id = auto_field(load_only=True)
    # invoice_id = auto_field(load_only=True)
    type = auto_field(required=True, validate=validate.OneOf(['deposit', 'withdrawal', 'transfer', 'payment']))
    status = auto_field(required=True, validate=validate.OneOf(['pending', 'completed', 'failed', 'cancelled']))
    amount = auto_field(required=True, validate=validate.Range(min=0.01))
    fee = auto_field(load_default=0.0, validate=validate.Range(min=0))
    description = auto_field()
    currency_code = auto_field(required=True, validate=validate.Length(equal=3))
    metadata = fields.Dict(allow_none=True)
    created_at = auto_field(dump_only=True)

    user = fields.Nested(User_schema(only=("id", "name", "email")), dump_only=True)
    debit_account = fields.Nested(AccountSchema(only=("id", "account_number_masked", "currency_code")), dump_only=True)
    credit_account = fields.Nested(AccountSchema(only=("id", "account_number_masked", "currency_code")), dump_only=True)
    payment_method = fields.Nested("PaymentMethodSchema", only=("id", "type", "provider"), dump_only=True)
    beneficiary = fields.Nested("BeneficiariesSchema", only=("id", "beneficiary_name", "bank_name"), dump_only=True)
    