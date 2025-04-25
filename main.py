from fastapi import FastAPI, Request
import logging

from core import setup_logging, verify_token
from api import test_router, expenses_router

# Setup global logging
setup_logging()
# buat logger khusus untuk middleware
mw_logger = logging.getLogger("request.middleware")

app = FastAPI()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    msg = f"Request: {request.method} {request.url.path} → {response.status_code}"
    # INFO untuk 200, ERROR untuk lainnya
    if response.status_code == 200:
        mw_logger.info(msg)
    else:
        mw_logger.error(msg)
    return response

# daftarkan router seperti biasa
app.include_router(test_router)
app.include_router(expenses_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8050, reload=True)
