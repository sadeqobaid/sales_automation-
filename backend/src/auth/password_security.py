"""
Author Sadeq Obaid and Abdallah Obaid

Password security module for the Sales Automation System.
This module provides functionality for password validation and security.
"""

import re
from typing import Dict, Any, List, Tuple
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordValidator:
    """Password validation and security class."""
    
    # Default password requirements
    MIN_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL_CHARS = True
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?/~`"
    
    @classmethod
    def validate_password(cls, password: str) -> Tuple[bool, List[str]]:
        """
        Validate a password against security requirements.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, list of validation errors)
        """
        errors = []
        
        # Check length
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters long")
        
        # Check for uppercase letters
        if cls.REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Check for lowercase letters
        if cls.REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        # Check for digits
        if cls.REQUIRE_DIGITS and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
        
        # Check for special characters
        if cls.REQUIRE_SPECIAL_CHARS and not any(c in cls.SPECIAL_CHARS for c in password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
    
    @classmethod
    def calculate_strength(cls, password: str) -> int:
        """
        Calculate password strength score (0-100).
        
        Args:
            password: Password to evaluate
            
        Returns:
            int: Strength score (0-100)
        """
        score = 0
        
        # Length score (up to 25 points)
        length_score = min(25, len(password) * 2)
        score += length_score
        
        # Character variety score (up to 50 points)
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in cls.SPECIAL_CHARS for c in password)
        
        variety_score = (has_upper + has_lower + has_digit + has_special) * 12.5
        score += variety_score
        
        # Complexity score (up to 25 points)
        complexity_score = 0
        
        # Check for non-sequential characters
        sequential_count = 0
        for i in range(1, len(password)):
            if ord(password[i]) == ord(password[i-1]) + 1:
                sequential_count += 1
        
        # Penalize sequential characters
        complexity_score += max(0, 15 - sequential_count * 3)
        
        # Reward for mixed character types
        char_type_changes = 0
        for i in range(1, len(password)):
            prev_is_alpha = password[i-1].isalpha()
            prev_is_digit = password[i-1].isdigit()
            prev_is_special = not prev_is_alpha and not prev_is_digit
            
            curr_is_alpha = password[i].isalpha()
            curr_is_digit = password[i].isdigit()
            curr_is_special = not curr_is_alpha and not curr_is_digit
            
            if prev_is_alpha != curr_is_alpha or prev_is_digit != curr_is_digit or prev_is_special != curr_is_special:
                char_type_changes += 1
        
        complexity_score += min(10, char_type_changes)
        
        score += complexity_score
        
        return min(100, score)
    
    @classmethod
    def get_strength_label(cls, strength: int) -> str:
        """
        Get a label for password strength.
        
        Args:
            strength: Strength score (0-100)
            
        Returns:
            str: Strength label
        """
        if strength < 40:
            return "Weak"
        elif strength < 70:
            return "Moderate"
        elif strength < 90:
            return "Strong"
        else:
            return "Very Strong"
    
    @classmethod
    def hash_password(cls, password: str) -> str:
        """
        Hash a password.
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        return pwd_context.hash(password)
    
    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against a hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            bool: True if password matches hash, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)


# Create validator instance
password_validator = PasswordValidator()
