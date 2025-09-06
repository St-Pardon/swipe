# save this as generate_key.py and run `python generate_key.py`
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode('utf-8'))
