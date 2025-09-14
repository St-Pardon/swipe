import os
from app.config import Config

class PaymentConfig:
    """Payment gateway configuration settings"""
    
    # Stripe Configuration - use actual test keys for development
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

    # Application URLs
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    WEBHOOK_BASE_URL = os.environ.get('WEBHOOK_BASE_URL', 'http://localhost:5000')
    
    # Supported currencies
    SUPPORTED_CURRENCIES = ['USD', 'EUR', 'GBP', 'NGN', 'CAD', 'AUD']
    
    # Payment limits
    MIN_PAYMENT_AMOUNT = {
        'USD': 0.50,
        'EUR': 0.50,
        'GBP': 0.30,
        'NGN': 100.00,
        'CAD': 0.50,
        'AUD': 0.50
    }
    
    MAX_PAYMENT_AMOUNT = {
        'USD': 999999.99,
        'EUR': 999999.99,
        'GBP': 999999.99,
        'NGN': 50000000.00,
        'CAD': 999999.99,
        'AUD': 999999.99
    }
    
    # Payout settings
    PAYOUT_CURRENCIES = ['USD', 'EUR', 'GBP', 'NGN']
    MIN_PAYOUT_AMOUNT = {
        'USD': 1.00,
        'EUR': 1.00,
        'GBP': 1.00,
        'NGN': 500.00
    }
    
    # Webhook settings
    WEBHOOK_TOLERANCE = 300  # 5 minutes tolerance for webhook timestamps
    
    @classmethod
    def is_currency_supported(cls, currency):
        """Check if currency is supported for payments"""
        return currency.upper() in cls.SUPPORTED_CURRENCIES
    
    @classmethod
    def is_payout_currency_supported(cls, currency):
        """Check if currency is supported for payouts"""
        return currency.upper() in cls.PAYOUT_CURRENCIES
    
    @classmethod
    def get_min_amount(cls, currency, operation='payment'):
        """Get minimum amount for currency and operation"""
        currency = currency.upper()
        if operation == 'payout':
            return cls.MIN_PAYOUT_AMOUNT.get(currency, 1.00)
        return cls.MIN_PAYMENT_AMOUNT.get(currency, 0.50)
    
    @classmethod
    def get_max_amount(cls, currency):
        """Get maximum payment amount for currency"""
        currency = currency.upper()
        return cls.MAX_PAYMENT_AMOUNT.get(currency, 999999.99)
    
    @classmethod
    def validate_amount(cls, amount, currency, operation='payment'):
        """Validate payment amount for currency"""
        currency = currency.upper()
        min_amount = cls.get_min_amount(currency, operation)
        max_amount = cls.get_max_amount(currency)
        
        if amount < min_amount:
            return False, f"Amount must be at least {min_amount} {currency}"
        
        if amount > max_amount:
            return False, f"Amount cannot exceed {max_amount} {currency}"
        
        return True, None
