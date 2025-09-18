from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field
from marshmallow import fields, validate
from app.models.beneficiaries_model import Beneficiaries
from app.schema.user_schema import User_schema
from app.schema.account_schema import AccountSchema
from app.extensions import db

class BeneficiariesSchema(SQLAlchemySchema):
    class Meta:
        model = Beneficiaries
        load_instance = True
        sqla_session = db.session

    id = auto_field(dump_only=True)
    user_id = auto_field(load_only=True, required=False)
    account_id = auto_field(load_only=True, required=True)
    bank_name = auto_field(required=True)
    account_number = auto_field(required=True)
    routing_number = auto_field(required=True)
    beneficiary_name = auto_field(required=True)
    created_at = auto_field(dump_only=True)

    user = fields.Nested(User_schema(only=("id", "name", "email")), dump_only=True)
    account = fields.Nested(AccountSchema(only=("id", "account_number_masked", "currency_code")), dump_only=True)
