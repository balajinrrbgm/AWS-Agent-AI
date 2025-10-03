import hashlib
import hmac
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class SecurityUtils:
    """
    Security utilities for authentication and data protection
    """
    
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.algorithm = "HS256"
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt
        """
        try:
            return pwd_context.hash(password)
        except Exception as e:
            logger.error(f"Error hashing password: {str(e)}")
            # Fallback to simple hash for development
            return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        """
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Error verifying password: {str(e)}")
            # Fallback verification for development
            return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)
        
        to_encode.update({"exp": expire})
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating access token: {str(e)}")
            raise
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.JWTError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None
    
    def generate_session_id(self) -> str:
        """
        Generate a secure session ID
        """
        return secrets.token_urlsafe(32)
    
    def generate_api_key(self) -> str:
        """
        Generate a secure API key
        """
        return secrets.token_urlsafe(48)
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """
        Simple encryption for sensitive data (placeholder)
        In production, use proper encryption with AWS KMS
        """
        # This is a simple obfuscation for development
        # In production, use proper encryption with AWS KMS
        key = self.secret_key.encode()[:32]  # Use first 32 bytes of secret key
        
        # Simple XOR "encryption" for development (NOT secure for production)
        encrypted = ""
        for i, char in enumerate(data):
            encrypted += chr(ord(char) ^ ord(key[i % len(key)]))
        
        # Base64 encode the result
        import base64
        return base64.b64encode(encrypted.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """
        Simple decryption for sensitive data (placeholder)
        """
        try:
            import base64
            # Decode from base64
            encrypted = base64.b64decode(encrypted_data.encode()).decode()
            
            key = self.secret_key.encode()[:32]
            
            # Reverse the XOR "encryption"
            decrypted = ""
            for i, char in enumerate(encrypted):
                decrypted += chr(ord(char) ^ ord(key[i % len(key)]))
            
            return decrypted
        except Exception as e:
            logger.error(f"Error decrypting data: {str(e)}")
            return ""
    
    def validate_input(self, input_data: str, max_length: int = 1000) -> bool:
        """
        Basic input validation
        """
        if not input_data:
            return False
        
        if len(input_data) > max_length:
            return False
        
        # Check for potentially malicious patterns
        malicious_patterns = [
            '<script',
            'javascript:',
            'onload=',
            'onerror=',
            'eval(',
            'document.cookie',
            'window.location'
        ]
        
        input_lower = input_data.lower()
        for pattern in malicious_patterns:
            if pattern in input_lower:
                return False
        
        return True
    
    def sanitize_input(self, input_data: str) -> str:
        """
        Sanitize user input
        """
        if not input_data:
            return ""
        
        # Remove potentially dangerous characters
        import html
        sanitized = html.escape(input_data)
        
        # Remove null bytes and control characters
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\r\t')
        
        return sanitized.strip()
    
    def log_security_event(
        self, 
        event_type: str, 
        user_id: str = None, 
        details: Dict[str, Any] = None
    ):
        """
        Log security-related events
        """
        event_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "details": details or {}
        }
        
        logger.info(f"Security Event: {event_data}")
    
    def generate_otp(self, length: int = 6) -> str:
        """
        Generate a one-time password
        """
        digits = "0123456789"
        return ''.join(secrets.choice(digits) for _ in range(length))
    
    def create_password_reset_token(self, user_id: str) -> str:
        """
        Create a password reset token
        """
        data = {
            "user_id": user_id,
            "type": "password_reset",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Short expiration for password reset tokens
        expires_delta = timedelta(hours=1)
        return self.create_access_token(data, expires_delta)
    
    def verify_password_reset_token(self, token: str) -> Optional[str]:
        """
        Verify a password reset token and return user ID
        """
        payload = self.verify_token(token)
        
        if payload and payload.get("type") == "password_reset":
            return payload.get("user_id")
        
        return None

# Global security utilities instance
security_utils = SecurityUtils()

def get_password_hash(password: str) -> str:
    """
    Convenience function to hash a password
    """
    return security_utils.hash_password(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Convenience function to verify a password
    """
    return security_utils.verify_password(plain_password, hashed_password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Convenience function to create an access token
    """
    return security_utils.create_access_token(data, expires_delta)

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to verify a token
    """
    return security_utils.verify_token(token)

def get_current_user(token: str) -> Optional[str]:
    """
    Get current user ID from token
    """
    payload = verify_token(token)
    if payload:
        return payload.get("user_id")
    return None