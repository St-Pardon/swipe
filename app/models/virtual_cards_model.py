from app.extensions import db
from app.utils.guid_utils import GUID
import uuid
from sqlalchemy_utils import EncryptedType
from app.config import Config

secret_key = Config.SECRET_KEY

class VirtualCard(db.Model):
    id = db.Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(GUID(), db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='virtual_cards')
    account_id = db.Column(GUID(), db.ForeignKey('account.id'), nullable=False)
    account = db.relationship('Account', back_populates='virtual_cards')
    card_type = db.Column(db.String(50), nullable=False)
    card_holder = db.Column(db.String(180), nullable=False)
    card_number = db.Column(EncryptedType(db.String(255), secret_key), nullable=False)
    expiration_date = db.Column(db.String(5), nullable=False)
    cvv = db.Column(EncryptedType(db.String(255), secret_key), nullable=False)
    pin = db.Column(EncryptedType(db.String(255), secret_key), nullable=False)
    spending_limit = db.Column(db.Float, nullable=True)
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
