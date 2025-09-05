from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.guid_utils import GUID
import uuid


class User(db.Model):
    id = db.Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    accountType = db.Column(db.String(120), nullable=False)
    country = db.Column(db.String(120), nullable=False)
    countryCode = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    accounts = db.relationship('Account', back_populates='user', cascade="all, delete-orphan", lazy='dynamic')
    virtual_cards = db.relationship('Virtual_Cards', back_populates='user', cascade="all, delete-orphan")
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
