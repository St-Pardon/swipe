from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field
from marshmallow import fields
from app.models.account_model import Account
from app.schema.user_schema import User_schema
from app.extensions import db


class AccountSchema(SQLAlchemySchema):
    class Meta:
        model = Account
        load_instance = True
        sqla_session = db.session

    id = auto_field(dump_only=True)
    user_id = auto_field(load_only=True, required=True)
    balance = auto_field()
    currency = auto_field()
    currency_code = auto_field()
    account_holder = auto_field()
    account_number = auto_field()
    routing_number = auto_field()
    bank_name = auto_field()
    accountType = auto_field()
    address = auto_field()
    is_default = auto_field()
    created_at = auto_field(dump_only=True)
    updated_at = auto_field(dump_only=True)

    user = fields.Nested(User_schema(only=("id", "name", "email")), dump_only=True)