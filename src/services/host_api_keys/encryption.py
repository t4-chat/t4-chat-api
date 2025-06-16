import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from src.services.common.errors import BadRequestError

from src.config import settings
from src.logging.logging_config import get_logger


class ApiKeyEncryption:
    """Helper class for encrypting and decrypting API keys."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._cipher = self._get_cipher()

    def _get_cipher(self) -> Fernet:
        """Create a Fernet cipher from the encryption key."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'agg_ai_salt',  # Static salt for consistency
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(settings.API_KEY_ENCRYPTION_KEY.encode()))
        return Fernet(key)

    def encrypt(self, api_key: str) -> str:
        """Encrypt an API key."""
        try:
            return self._cipher.encrypt(api_key.encode()).decode()
        except Exception as e:
            self.logger.error(f"Failed to encrypt API key: {str(e)}")
            raise BadRequestError("Failed to encrypt API key")

    def decrypt(self, encrypted_key: str) -> str:
        """Decrypt an API key."""
        try:
            return self._cipher.decrypt(encrypted_key.encode()).decode()
        except Exception as e:
            self.logger.error(f"Failed to decrypt API key: {str(e)}")
            raise BadRequestError("Failed to decrypt API key") 