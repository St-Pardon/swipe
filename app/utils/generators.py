import hashlib
import secrets
import string
import uuid

class AccountNumberGenerator:
    @staticmethod
    def generate_account_number(user_id, bank_code):
        """
        Generate a unique account number that includes:
        - Bank identification prefix
        - User identifier component
        - Random sequence
        - Check digit for validation
        """
        # Bank identifier (first 4 digits)
        bank_prefix = bank_code[:4].zfill(4)
        
        # User identifier component (next 4 digits)
        # user_id is a string UUID from the JWT, convert it to an integer for the modulo operation.
        user_uuid = uuid.UUID(user_id)
        user_component = str(user_uuid.int % 10000).zfill(4)
        
        # Random sequence (next 6 digits)
        random_seq = ''.join(secrets.choice(string.digits) for _ in range(6))
        
        # Combine and add check digit
        partial_account = bank_prefix + user_component + random_seq
        check_digit = AccountNumberGenerator._calculate_luhn_check_digit(partial_account)
        
        account_number = partial_account + check_digit
        
        return account_number
    
    @staticmethod
    def _calculate_luhn_check_digit(number):
        """Calculate Luhn check digit for validation"""
        def digits_of(n):
            return [int(d) for d in str(n)]
        
        digits = digits_of(number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d*2))
        return str((10 - (checksum % 10)) % 10)
    
    @staticmethod
    def generate_hash(account_number):
        """Generate a hash for uniqueness checking"""
        return hashlib.sha256(account_number.encode()).hexdigest()
