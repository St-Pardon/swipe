from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field
from marshmallow import fields, post_load, validate
from app.models.user_model import User
from app.models.account_model import Account
from app.extensions import db
from werkzeug.security import generate_password_hash



class User_schema(SQLAlchemySchema):
    class Meta:
        model = User
        load_instance = True
        sqla_session = db.session

    id = auto_field(dump_only=True)
    email = auto_field()
    password = fields.String(load_only=True, required=True)
    name = auto_field()
    accountType = auto_field()
    country = auto_field()
    countryCode = auto_field()
    city = auto_field()
    role = auto_field(load_default='user', validate=validate.OneOf(['user', 'admin']))
    address = auto_field()
    phone = auto_field()

    @post_load
    def hash_password(self, user, **kwargs):
        """
        Hashes the password of the User instance after it has been loaded
        and assigns the hashed password back to the user object.
        
        Args:
            user (User): The User model instance created by Marshmallow.
                         This is the object we modify before it's committed.
        """
        # user.password is the plain-text password from the loaded data.
        # We use the model's set_password method to hash it.
        user.set_password(user.password)
        return user
