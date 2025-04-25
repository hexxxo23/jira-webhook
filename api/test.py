from fastapi import APIRouter
import logging
from services.odoo_client import get_client

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/test")
def test():
    logger.info("Endpoint /test diakses")
    return {"message": "Hello, FastApi!"}

@router.get("/")
def read_root():
    client = get_client()
    logger.info("Endpoint / diakses, client=%s", client)
    return {"message": "Hello, FastApi!"}
