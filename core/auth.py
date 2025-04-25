# core/auth.py
import os
from dotenv import load_dotenv
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException
import logging

# load .env
load_dotenv()

security = HTTPBearer()
EXPECTED_TOKEN = os.getenv("EXPECTED_TOKEN")

def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    if credentials.credentials != EXPECTED_TOKEN:
        logging.getLogger(__name__).warning("Invalid token: %s", credentials.credentials)
        raise HTTPException(status_code=403, detail="Invalid token")
    return credentials.credentials
