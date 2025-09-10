from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field
from marshmallow import fields, validate
from app.models.payment_methods_model import PaymentMethod
from app.extensions import db
from app.schema.user_schema import User_schema

class PaymentMethodScema(SQLAlchemySchema):
    class Meta:
        model = PaymentMethod
        load_instance = True
        sqla_session = db.session

    id = auto_field(dump_only=True)
    user_id = auto_field(load_only=True, required=True)
    type = auto_field(required=True, validate=validate.OneOf(['card', 'bank_account', 'mobile_money']))
    provider = auto_field()
    external_id = auto_field()
    details = auto_field()
    is_default = auto_field(load_default=False)
    created_at = auto_field(dump_only=True)
    updated_at = auto_field(dump_only=True)

    user = fields.Nested(User_schema(only=("id", "name", "email")), dump_only=True)