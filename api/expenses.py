from fastapi import APIRouter, HTTPException, Request, Depends
import logging, json
from datetime import datetime
from schema.jira_models import JiraRequest
from services.odoo_client import find_data, create_data
from main import verify_token  # ambil verifier dari main

router = APIRouter(prefix="/jira", tags=["jira"])
logger = logging.getLogger(__name__)

@router.post("/expenses")
async def create_expense(
    payload: JiraRequest,
    request: Request,
    token: str = Depends(verify_token),  # gunakan verify_token dari main
):
    logger.info("Endpoint /jira/expenses diakses")
    body = await request.json()
    logger.info("Raw payload:\n%s", json.dumps(body, indent=2))

    # Transformasi payload
    try:
        p = payload.fields
        transformed = {
            "key": payload.key,
            "summary": p.summary,
            "project_id": p.project_id.get("value") if p.project_id else None,
            "issue_type": p.issue_type.name,
            "status": {
                "name": p.status.name,
                "status_category": {"name": p.status.status_category.name},
            },
            "reporter": {
                "display_name": p.reporter.display_name if p.reporter else None,
                "email": p.reporter.email if p.reporter else None,
                "account_id": p.reporter.account_id if p.reporter else None,
                "active": p.reporter.active if p.reporter else None,
            },
            "total_payment": p.total_payment,
            "actual_expense": p.actual_expense,
            "done_at": p.done_at.isoformat() if p.done_at else None,
        }
        logger.info("Transformed:\n%s",
                    json.dumps(transformed, indent=2, ensure_ascii=False))
    except Exception as e:
        logger.error("Parsing error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    # Logic Odoo: buat hr.expense
    try:
        existing = find_data("hr.expense", [("name", "=", transformed["key"])], ["id"])
        if existing:
            logger.warning("Expense already exists: %s", transformed["key"])
            return {"status": "Expense Already Exists"}

        data = {
            "name": transformed["key"],
            "date": datetime.now().strftime("%Y-%m-%d"),
            "total_amount_currency": transformed["total_payment"],
            "description": transformed["summary"],
        }
        rec_id = create_data("hr.expense", values=data)
        return {"status": f"Expense Created With id {rec_id}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating expense: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error Creating Expense")
