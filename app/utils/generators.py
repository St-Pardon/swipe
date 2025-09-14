import hashlib
import secrets
import string
import uuid

class AccountNumberGenerator:
    @staticmethod
    def generate_account_number(user_id, bank_code):
        """
        Generate a unique 10-digit account number that includes:
        - 4-digit Bank identification prefix
        - 3-digit User identifier component
        - 2-digit Random sequence
        - 1-digit Luhn check digit for validation
        """
        # Bank identifier (first 4 digits)
        bank_prefix = bank_code[:4].zfill(4)

        # User identifier component (next 3 digits)
        # user_id is a string UUID from the JWT, convert it to an integer for the modulo operation.
        user_uuid = uuid.UUID(user_id)
        user_component = str(user_uuid.int % 1000).zfill(3)

        # Random sequence (next 2 digits)
        random_seq = ''.join(secrets.choice(string.digits) for _ in range(2))

        # Combine and add check digit (final 1 digit)
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


class CardNumberGenerator:
    @staticmethod
    def generate_card_number(user_id: str, bin_prefix: str = "543200", length: int = 16) -> str:
        """
        Generate a 16-digit card number (internal use) using:
        - 6-digit BIN prefix
        - 6-digit user-based component
        - variable random digits to reach (length-1)
        - 1-digit Luhn check digit
        """
        # Normalize BIN to 6 digits
        bin_part = (bin_prefix or "").strip()[:6].ljust(6, '0')

        # Derive a 6-digit component from user UUID for stability per-user
        user_uuid = uuid.UUID(user_id)
        user_component = str(user_uuid.int % 1_000_000).zfill(6)

        # Fill remaining digits (excluding check digit)
        target_without_check = length - 1
        base = bin_part + user_component
        remaining = max(0, target_without_check - len(base))
        random_seq = ''.join(secrets.choice(string.digits) for _ in range(remaining))

        partial = (base + random_seq)[:target_without_check]
        check_digit = AccountNumberGenerator._calculate_luhn_check_digit(partial)

        return partial + check_digit
