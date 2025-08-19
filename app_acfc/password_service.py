from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

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
