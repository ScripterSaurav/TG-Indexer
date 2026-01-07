# token_util.py - Add path-based token support
import hmac
import hashlib
import time
import base64
import logging

from .config import SECRET_KEY, token_lifetime, token_validation_enabled

log = logging.getLogger(__name__)

def generate_download_token(chat_id: int, file_id: int) -> str:
    """Generate a simple time-limited download token"""
    if not token_validation_enabled:
        return ""
    
    try:
        # Simple payload: chat_id:file_id:timestamp
        timestamp = str(int(time.time()))
        payload = f"{chat_id}:{file_id}:{timestamp}"
        
        # Create signature
        signature = hmac.new(
            SECRET_KEY.encode(),
            payload.encode(),
            hashlib.sha256
        ).digest()
        
        # Combine and encode
        token_data = f"{payload}:{base64.urlsafe_b64encode(signature).decode()}"
        return base64.urlsafe_b64encode(token_data.encode()).decode()
    except Exception as e:
        log.error(f"Error generating token: {e}")
        return ""

def validate_download_token(token: str, chat_id: int, file_id: int) -> bool:
    """Validate a download token - works with both query param and path token"""
    if not token_validation_enabled:
        return True
    
    if not token:
        log.debug("No token provided")
        return False
    
    try:
        # Decode token
        token_data = base64.urlsafe_b64decode(token.encode()).decode()
        parts = token_data.split(':')
        
        if len(parts) != 4:
            log.debug(f"Invalid token format: expected 4 parts, got {len(parts)}")
            return False
            
        token_chat_id, token_file_id, timestamp, provided_signature = parts
        
        # Check expiration
        current_time = int(time.time())
        token_time = int(timestamp)
        
        if current_time - token_time > token_lifetime:
            log.debug(f"Token expired: {current_time - token_time}s old, max {token_lifetime}s")
            return False
        
        # Verify chat_id and file_id match
        if int(token_chat_id) != chat_id or int(token_file_id) != file_id:
            log.debug(f"Token chat/file ID mismatch: {token_chat_id} != {chat_id} or {token_file_id} != {file_id}")
            return False
        
        # Verify signature
        expected_payload = f"{chat_id}:{file_id}:{timestamp}"
        expected_signature = hmac.new(
            SECRET_KEY.encode(),
            expected_payload.encode(),
            hashlib.sha256
        ).digest()
        
        provided_signature_bytes = base64.urlsafe_b64decode(provided_signature.encode())
        
        if not hmac.compare_digest(expected_signature, provided_signature_bytes):
            log.debug("Token signature mismatch")
            return False
        
        log.debug("Token validation successful")
        return True
        
    except Exception as e:
        log.debug(f"Token validation error: {e}")
        return False

def extract_token_from_path(path: str) -> str:
    """Extract token from URL path (for external players)"""
    if not token_validation_enabled:
        return ""
    
    # Check if path contains a token (looks like base64 string)
    parts = path.strip('/').split('/')
    
    # Scenario 1: Token at the beginning - /token/alias/file_id/filename
    if len(parts) >= 4:
        first_part = parts[0]
        if len(first_part) > 20 and '=' in first_part:  # Likely a base64 token
            return first_part
    
    # Scenario 2: Token at the end - /alias/file_id/filename/token  
    if len(parts) >= 4:
        last_part = parts[-1]
        if len(last_part) > 20 and '=' in last_part:  # Likely a base64 token
            return last_part
    
    return ""
