from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException
import logging

security = HTTPBearer()
EXPECTED_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkppcmEgQVBJIFRva2VuIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    if credentials.credentials != EXPECTED_TOKEN:
        logging.getLogger(__name__).warning("Invalid token: %s", credentials.credentials)
        raise HTTPException(status_code=403, detail="Invalid token")
    return credentials.credentials
