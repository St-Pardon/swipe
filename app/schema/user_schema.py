from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field
from marshmallow import fields, post_load, validate
from app.models.user_model import User
from app.models.account_model import Account
from app.extensions import db
from werkzeug.security import generate_password_hash



class User_schema(SQLAlchemySchema):
    class Meta:
        model = User
        sqla_session = db.session

    id = auto_field(dump_only=True)
    email = auto_field()
    password = fields.String(load_only=True, required=True)
    name = auto_field()
    accountType = auto_field(validate=validate.OneOf(['freelancer', 'company']))
    country = auto_field()
    countryCode = auto_field()
    city = auto_field()
    role = auto_field(validate=validate.OneOf(['user', 'admin']))
    address = auto_field()
    phone = auto_field()

    @post_load
    def create_user(self, data, **kwargs):
        """
        Creates a User instance and hashes the password.
        """
        password = data.pop('password')
        user = User(**data)
        user.set_password(password)
        return user
