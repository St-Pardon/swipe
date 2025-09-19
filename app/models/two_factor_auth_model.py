import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.extensions import db
import pyotp
import qrcode
from io import BytesIO
import base64

class TwoFactorAuth(db.Model):
    __tablename__ = 'two_factor_auth'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('user.id'), nullable=False, unique=True)
    secret_key = Column(String(32), nullable=False)
    is_enabled = Column(Boolean, default=False, nullable=False)
    backup_codes = Column(Text)  # JSON string of backup codes
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="two_factor_auth")
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.secret_key = pyotp.random_base32()
        self.is_enabled = False
        
    def get_totp_uri(self, user_email, issuer_name="Swipe Payment"):
        """Generate TOTP URI for QR code"""
        return pyotp.totp.TOTP(self.secret_key).provisioning_uri(
            name=user_email,
            issuer_name=issuer_name
        )
    
    def get_qr_code(self, user_email, issuer_name="Swipe Payment"):
        """Generate QR code as base64 string"""
        uri = self.get_totp_uri(user_email, issuer_name)
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    def verify_token(self, token):
        """Verify TOTP token"""
        totp = pyotp.TOTP(self.secret_key)
        return totp.verify(token, valid_window=1)  # Allow 30 second window
    
    def generate_backup_codes(self, count=8):
        """Generate backup codes"""
        import secrets
        import json
        
        codes = []
        for _ in range(count):
            code = ''.join([str(secrets.randbelow(10)) for _ in range(8)])
            codes.append(code)
        
        self.backup_codes = json.dumps(codes)
        return codes
    
    def verify_backup_code(self, code):
        """Verify and consume backup code"""
        import json
        
        if not self.backup_codes:
            return False
            
        codes = json.loads(self.backup_codes)
        if code in codes:
            codes.remove(code)
            self.backup_codes = json.dumps(codes)
            db.session.commit()
            return True
        return False
    
    def get_remaining_backup_codes(self):
        """Get count of remaining backup codes"""
        import json
        
        if not self.backup_codes:
            return 0
        return len(json.loads(self.backup_codes))

class TwoFactorAttempt(db.Model):
    __tablename__ = 'two_factor_attempts'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('user.id'), nullable=False)
    ip_address = Column(String(45))  # IPv6 compatible
    success = Column(Boolean, nullable=False)
    attempt_type = Column(String(20), nullable=False)  # 'totp', 'backup_code'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User")
    
    @classmethod
    def log_attempt(cls, user_id, ip_address, success, attempt_type):
        """Log 2FA attempt"""
        attempt = cls(
            user_id=user_id,
            ip_address=ip_address,
            success=success,
            attempt_type=attempt_type
        )
        db.session.add(attempt)
        db.session.commit()
        return attempt
    
    @classmethod
    def get_recent_failed_attempts(cls, user_id, minutes=15):
        """Get recent failed attempts for rate limiting"""
        since = datetime.utcnow() - timedelta(minutes=minutes)
        return cls.query.filter(
            cls.user_id == user_id,
            cls.success == False,
            cls.created_at >= since
        ).count()
