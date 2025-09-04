from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field
from marshmallow import fields, post_load
from app.models.user_model import User
from werkzeug.security import generate_password_hash



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
    def hash_password(self, user, **kwargs):
        """
        Hashes the password of the User instance after it has been loaded
        and assigns the hashed password back to the user object.
        
        Args:
            user (User): The User model instance created by Marshmallow.
                         This is the object we modify before it's committed.
        """
        # We access the password attribute directly from the 'user' object.
        # We also use 'generate_password_hash' to properly hash the password.
        user['password'] = generate_password_hash(user['password'])
        return user
