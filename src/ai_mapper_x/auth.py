# User authentication

from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from fastapi import  Depends, status, HTTPException
import secrets
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError
import os
import time, hmac, hashlib


AIMAPPER_API_KEY = os.environ.get("AIMAPPER_API_KEY", "aimapper-api-key")


# RS256 public key
KEY_DIR = os.path.join(os.path.dirname(__file__), "security_keys")
with open(f"{KEY_DIR}/public.pem") as f:
    PUBLIC_KEY = f.read()


security_basic = HTTPBasic(auto_error=False)
security_bearer = HTTPBearer(auto_error=False)


ALGORITHM = "RS256"
# --- Auth Check ---
def get_auth_method(
    basic_credentials: Optional[HTTPBasicCredentials] = Depends(security_basic),
    bearer_credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)
):
    # Basic Auth with api key
    if basic_credentials:
        if (
            secrets.compare_digest(basic_credentials.username, "apikey") and
            secrets.compare_digest(basic_credentials.password, AIMAPPER_API_KEY)
        ):
            return {"method": "basic", "user": basic_credentials.username}

    # Bearer Token
    if bearer_credentials:
        token = bearer_credentials.credentials
        try:
            payload = jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
            return {"method": "bearer", "token_payload": payload}
        except ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Bearer token expired")
        except JWTError:
            pass  

    # If neither works
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized. Provide a valid API key or Bearer token.",
        headers={"WWW-Authenticate": "Basic, Bearer"},
    )


# FOR DOWNLOAD MXL 
def create_signed_url(mxl_id: str, expiry_seconds=300):
    expires = int(time.time()) + expiry_seconds
    data = f"{mxl_id}:{expires}"
    signature = hmac.new(AIMAPPER_API_KEY.encode(), data.encode(), hashlib.sha256).hexdigest()
    return f"/map/download/{mxl_id}?expires={expires}&signature={signature}"


def verify_signed_link(mxl_id: str, expires: int, signature: str):
    expected = hmac.new(
        AIMAPPER_API_KEY.encode(),
        f"{mxl_id}:{expires}".encode(),
        hashlib.sha256
    ).hexdigest()

    if time.time() > expires or not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=403, detail="Invalid or expired link")
    
    return True