from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field
from marshmallow import fields, post_load
from models.user_model import User


class User_schema(SQLAlchemySchema):
    class Meta:
        model = User
        load_instance = True

    id = auto_field(dump_only=True)
    email = auto_field()
    password = fields.String(load_only=True, required=True)
    name = auto_field()
    accountType = auto_field()
    country = auto_field()
    countryCode = auto_field()
    city = auto_field()
    address = auto_field()
    phone = auto_field()

    @post_load
    def hash_password(self, data, **kwargs):
        if "password" in data:
            user = User(**data)
            user.set_password(data["password"])
            return user
        return data
