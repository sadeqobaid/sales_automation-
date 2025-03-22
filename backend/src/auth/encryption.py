"""
Author Sadeq Obaid and Abdallah Obaid

Data encryption module for the Sales Automation System.
This module provides functionality for encrypting sensitive data.
"""

import base64
import os
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from config.settings import ENCRYPTION_KEY, ENCRYPTION_SALT


class DataEncryption:
    """Data encryption handler for sensitive information."""
    
    def __init__(self, key: Optional[str] = None, salt: Optional[bytes] = None):
        """
        Initialize the encryption handler.
        
        Args:
            key: Encryption key (defaults to ENCRYPTION_KEY from settings)
            salt: Encryption salt (defaults to ENCRYPTION_SALT from settings)
        """
        self.key = key or ENCRYPTION_KEY
        self.salt = salt or base64.b64decode(ENCRYPTION_SALT)
        self.fernet = self._create_fernet()
    
    def _create_fernet(self) -> Fernet:
        """
        Create a Fernet instance for encryption/decryption.
        
        Returns:
            Fernet: Fernet instance
        """
        # Derive a key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(self.key.encode()))
        return Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            str: Encrypted data (base64 encoded)
        """
        if not data:
            return data
            
        encrypted_data = self.fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt data.
        
        Args:
            encrypted_data: Encrypted data (base64 encoded)
            
        Returns:
            str: Decrypted data
            
        Raises:
            ValueError: If decryption fails
        """
        if not encrypted_data:
            return encrypted_data
            
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data)
            decrypted_data = self.fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
    
    @staticmethod
    def generate_key() -> str:
        """
        Generate a new encryption key.
        
        Returns:
            str: Base64 encoded encryption key
        """
        key = Fernet.generate_key()
        return base64.urlsafe_b64encode(key).decode()
    
    @staticmethod
    def generate_salt() -> str:
        """
        Generate a new encryption salt.
        
        Returns:
            str: Base64 encoded encryption salt
        """
        salt = os.urandom(16)
        return base64.urlsafe_b64encode(salt).decode()


# Create encryption handler instance
data_encryption = DataEncryption()
