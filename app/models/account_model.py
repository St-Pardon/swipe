from sqlite3 import IntegrityError
from app.extensions import db
from app.utils.generators import AccountNumberGenerator
from app.utils.guid_utils import GUID
import uuid
from cryptography.fernet import Fernet
from app.config import Config
from app.models.virtual_cards_model import VirtualCard

ACCOUNT_ENCRYPTION_KEY = Config.ACCOUNT_ENCRYPTION_KEY


class Account(db.Model):
    id = db.Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(GUID(), db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='accounts')
    balance = db.Column(db.Float, nullable=False, default=0.0)
    currency = db.Column(db.String(3), nullable=False)
    currency_code = db.Column(db.String(3), nullable=False)
    account_holder = db.Column(db.String(180), nullable=False)
    account_number = db.Column(db.LargeBinary, nullable=False)
    account_number_hash = db.Column(db.String(64), unique=True, nullable=False)
    routing_number = db.Column(db.String(80), nullable=True)
    bank_name = db.Column(db.String(255), nullable=False)
    accountType = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    virtual_cards = db.relationship('VirtualCard', back_populates='account', cascade="all, delete-orphan")
    debit_transactions = db.relationship('Transaction', foreign_keys='Transaction.debit_account_id', back_populates='debit_account', cascade="all, delete-orphan")
    credit_transactions = db.relationship('Transaction', foreign_keys='Transaction.credit_account_id', back_populates='credit_account', cascade="all, delete-orphan")
    view = db.relationship('TransactionView', back_populates='account')
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())

    _key_from_config = ACCOUNT_ENCRYPTION_KEY
    if not _key_from_config:
        _encryption_key = Fernet.generate_key()
    else:
        # Key from config must be encoded to bytes use script.py to generate key
        _encryption_key = _key_from_config.encode('utf-8')
    _cipher_suite = Fernet(_encryption_key)

    def set_account_number(self, account_number):
        """Encrypt and set account number with uniqueness check"""
        # check uniiquness and generate hash
        account_hash = AccountNumberGenerator.generate_hash(account_number)

        # Check if this hash already exists
        existing_account = Account.query.filter_by(account_number_hash=account_hash).first()
        if existing_account and existing_account.id != self.id:
            raise ValueError("Account number already exists")

        # Encrypt the account number on db
        encrypted_account = self._cipher_suite.encrypt(account_number.encode())

        self.account_number = encrypted_account
        self.account_number_hash = account_hash

    def get_account_number(self):
        """Decrypt and return account number"""
        if not self.account_number:
            return None
        decrypted_account = self._cipher_suite.decrypt(self.account_number)
        return decrypted_account.decode()

    @classmethod
    def create_account(cls, user_id, bank_code, **kwargs):
        """Create a new account with a unique account number"""
        max_retries = 10
        retries = 0
        
        while retries < max_retries:
            try:
                # Generate account number
                account_number = AccountNumberGenerator.generate_account_number(user_id, bank_code)
                
                # Create account instance
                account = cls(user_id=user_id, **kwargs)
                account.set_account_number(account_number)
                

                db.session.add(account)
                return account
                
            except IntegrityError:
                # Unique constraint violated, retry with a new number
                db.session.rollback()
                retries += 1
            except ValueError as e:
                # Account number already exists, retry until unique
                db.session.rollback()
                retries += 1
        
        raise Exception("Failed to create account after multiple attempts")
