from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from typing import Optional

from app.services.config.config_loader import config

# Create API key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    """
    Validate API key from header against config.ini
    """
    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key header is missing"
        )
    
    # Get valid API keys from config
    try:
        valid_api_keys = config['apikey']['key']
        # Split by comma and strip whitespace
        valid_keys_list = [key.strip() for key in valid_api_keys.split(',')]
        if api_key_header not in valid_keys_list:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API Key"
            )
    except (KeyError, Exception) as e:
        # If config section doesn't exist or other error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating API key: {str(e)}"
        )
    
    return api_key_header