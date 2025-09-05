from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field
from marshmallow import fields
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
    user_id = auto_field(load_only=True, required=True)
    account_id = auto_field(load_only=True, required=True)
    card_type = auto_field(required=True)
    card_holder = auto_field(required=True)
    card_number = auto_field(required=True)
    expiration_date = auto_field(required=True)
    cvv = auto_field(required=True)
    pin = auto_field(required=True)
    spending_limit = auto_field()
    is_default = auto_field()
    is_active = auto_field()
    created_at = auto_field(dump_only=True)

    user = fields.Nested(User_schema(only=("id", "name", "email")), dump_only=True)
    account = fields.Nested(AccountSchema(only=("id", "account_number", "bank_name")), dump_only=True)
