import bcrypt

class Auth:
    @staticmethod
    def hash_password(plain_password: str) -> str:
        """
        Hash a plaintext password for storing.
        Returns the hashed password as a string.
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plaintext password against the stored hashed password.
        Returns True if match, else False.
        """
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
