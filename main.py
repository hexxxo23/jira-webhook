from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from core.logger import setup_logging

# ===== Token & Verifier didefinisikan di main.py =====
security = HTTPBearer()
EXPECTED_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkppcmEgQVBJIFRva2VuIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    if credentials.credentials != EXPECTED_TOKEN:
        logging.getLogger(__name__).warning("Token tidak valid: %s", credentials.credentials)
        raise HTTPException(status_code=403, detail="Invalid token")
    return credentials.credentials
# =====================================================

# Setup logging global
setup_logging()

app = FastAPI()

# Middleware untuk log tiap request
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger = logging.getLogger("uvicorn.access")
    response = await call_next(request)
    level = logging.INFO if response.status_code == 200 else logging.ERROR
    logger.log(level, "Request: %s %s → %s", request.method, request.url.path, response.status_code)
    return response

# Import router setelah verifier agar tidak circular import error
from api.test import router as test_router
from api.expenses import router as expenses_router

# Registrasi semua router
app.include_router(test_router)
app.include_router(expenses_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8050, reload=True)
