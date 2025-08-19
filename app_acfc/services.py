from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask import Flask
from os import getenv

class PasswordService:
    def __init__(self):
        self.hasher = PasswordHasher(
            time_cost=4,
            memory_cost=2**16,
            parallelism=3,
            hash_len=32,
            salt_len=16
        )

    def hash_password(self, password: str) -> str:
        return self.hasher.hash(password)

    def verify_password(self, pwd: str, hashed_pwd: str) -> bool:
        try:
            self.hasher.verify(hashed_pwd, pwd)
            return True
        except VerifyMismatchError:
            return False
    
    def needs_rehash(self, hashed_pwd: str) -> bool:
        return self.hasher.check_needs_rehash(hashed_pwd)

class SecureSessionService:
    def __init__(self, app: Flask):
        self.app = app
        self.app.secret_key = getenv('SESSION_PASSKEY', 'default_secret_key')
        self.app.config['SESSION_TYPE'] = 'filesystem'
        self.app.config['SESSION_PERMANENT'] = False
        self.app.config['SESSION_USE_SIGNER'] = True
        # self.app.config['SESSION_COOKIE_SECURE'] = True #TODO Décommenter quand passage en production
        self.app.config['SESSION_COOKIE_HTTPONLY'] = True
        self.app.config['SESSION_COOKIE_NAME'] = 'acfc'
        self.app.config['PERMANENT_SESSION_LIFETIME'] = 1800
