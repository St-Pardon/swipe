from app.extensions import db
from app.utils.guid_utils import GUID
import uuid
import hashlib
from datetime import datetime, timedelta
from app.config import Config
from cryptography.fernet import Fernet
from app.utils.generators import CardNumberGenerator

# Access config values safely with proper error handling
try:
    from app.config import Config
    secret_key = getattr(Config, 'SECRET_KEY', '')
    ACCOUNT_ENCRYPTION_KEY = getattr(Config, 'ACCOUNT_ENCRYPTION_KEY', '')
except (ImportError, AttributeError) as e:
    secret_key = ''
    ACCOUNT_ENCRYPTION_KEY = ''

class VirtualCard(db.Model):
    id = db.Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(GUID(), db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='virtual_cards')
    account_id = db.Column(GUID(), db.ForeignKey('account.id'), nullable=False)
    account = db.relationship('Account', back_populates='virtual_cards')
    payment_intents = db.relationship('PaymentIntent', back_populates='virtual_card', cascade="all, delete-orphan")
    card_kind = db.Column(db.String(50), nullable=False)  # 'virtual' or 'physical'
    card_type = db.Column(db.String(50), nullable=False)  # 'debit' or 'credit'
  
    card_holder = db.Column(db.String(180), nullable=False)    
    _card_number = db.Column("card_number", db.LargeBinary, nullable=False)
    card_number_hash = db.Column(db.String(64), unique=True, nullable=False)
    expiration_date = db.Column(db.String(7), nullable=False) # MM/YYYY
    _cvv = db.Column("cvv", db.LargeBinary, nullable=False)
    _pin = db.Column("pin", db.LargeBinary, nullable=False)
    spending_limit = db.Column(db.Float, nullable=True)
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    stripe_payment_method_id = db.Column(db.String(255), nullable=True)  # Stripe payment method ID
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    # Initialize encryption with safe fallbacks
    try:
        _key_from_config = ACCOUNT_ENCRYPTION_KEY
        if not _key_from_config or _key_from_config == 'dev-encryption-key-change-in-production':
            _encryption_key = Fernet.generate_key()
        else:
            # Key from config should be a base64-encoded string
            try:
                _encryption_key = _key_from_config.encode('utf-8')
                # Test if it's a valid Fernet key
                Fernet(_encryption_key)
            except Exception:
                # If invalid, generate a new key
                _encryption_key = Fernet.generate_key()
        _cipher_suite = Fernet(_encryption_key)
    except Exception as e:
        # Ultimate fallback - generate a new key
        _encryption_key = Fernet.generate_key()
        _cipher_suite = Fernet(_encryption_key)
    
    def __init__(self, **kwargs):
        super(VirtualCard, self).__init__(**kwargs)
        # Only set a default PIN if one isn't provided during creation
        if not self._pin:
            self.pin = '0000'
        self.set_expiration_date()
    
    @property
    def card_number(self):
        """Decrypts and returns the card number."""
        if not self._card_number:
            return None
        return self._cipher_suite.decrypt(self._card_number).decode()
    
    @card_number.setter
    def card_number(self, card_number_plain):
        """Encrypts the card number and stores its hash for uniqueness checks."""
        card_hash = hashlib.sha256(card_number_plain.encode()).hexdigest()
        
        existing_card = VirtualCard.query.filter_by(card_number_hash=card_hash).first()
        if existing_card and existing_card.id != self.id:
            raise ValueError("Card number already exists")
        self._card_number = self._cipher_suite.encrypt(card_number_plain.encode())
        self.card_number_hash = card_hash
    
    @property
    def cvv(self):
        """Decrypts and returns the CVV."""
        if not self._cvv:
            return None
        return self._cipher_suite.decrypt(self._cvv).decode()
    
    @cvv.setter
    def cvv(self, cvv_plain):
        """Encrypts and sets the CVV."""
        self._cvv = self._cipher_suite.encrypt(str(cvv_plain).encode())
    
    @property
    def pin(self):
        """Decrypts and returns the PIN."""
        if not self._pin:
            return None
        return self._cipher_suite.decrypt(self._pin).decode()
    
    @pin.setter
    def pin(self, pin_plain):
        """Encrypts and sets the PIN."""
        self._pin = self._cipher_suite.encrypt(str(pin_plain).encode())
    
    def set_expiration_date(self):
        """
        Sets the expiration date to 3 years from the creation month.
        """
        creation_time = self.created_at or datetime.utcnow()
        expiration = creation_time + timedelta(days=3*365)
        self.expiration_date = expiration.strftime('%m/%Y')
    
    @staticmethod
    def generate_card_number(user_id):
        """Generate a unique 16-digit card number (internal use only)."""
        # Use dedicated card number generator (BIN + user-derived + random + Luhn)
        return CardNumberGenerator.generate_card_number(user_id, bin_prefix="543200", length=16)