import logging
import json
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Depends
from schema.jira_models import JiraRequest
from services.odoo_client import find_data, create_data
from core.auth import verify_token    # ambil dari core.auth

_logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jira", tags=["jira"])


@router.post("/expenses")
async def create_expense(
    payload: JiraRequest,
    request: Request,
    token: str = Depends(verify_token),
):
    _logger.info("Endpoint /jira/expenses diakses")

    request_json = await request.json()
    formatted_json = json.dumps(request_json, indent=2)
    _logger.info("Data Jira diterima: \n%s", formatted_json)
    try:
        # Transformasi data sesuai dengan mapping yang diinginkan
        try:
            transformed = {
                "self": payload.self_,
                "id": payload.id,
                "key": payload.key,
                "project_id": payload.fields.project_id.get("value") if payload.fields.project_id else None,
                "issue_type": payload.fields.issue_type.name if payload.fields.issue_type else None,
                "status": {
                    "name": payload.fields.status.name,
                    "status_category": {
                        "name": payload.fields.status.status_category.name
                    }
                },
                "reporter": {
                    "display_name": payload.fields.reporter.display_name if payload.fields.reporter else None,
                    "email": payload.fields.reporter.email if payload.fields.reporter else None,
                    "account_id": payload.fields.reporter.account_id if payload.fields.reporter else None,
                    "active": payload.fields.reporter.active if payload.fields.reporter else None,
                },
                "project": payload.fields.project.get("name") if payload.fields.project else None,
                "total_payment": payload.fields.total_payment,
                "total_payment_words": payload.fields.total_payment_words,
                "down_payment": payload.fields.down_payment,
                "down_payment_words": payload.fields.down_payment_words,
                "balance": payload.fields.balance,
                "balance_words": payload.fields.balance_words,
                "actual_expense": payload.fields.actual_expense,
                "actual_expense_words": payload.fields.actual_expense_words,
                "done_at": payload.fields.done_at.isoformat() if payload.fields.done_at else None,
                "summary": payload.fields.summary,
            }
            # Format the transformed data for better readability in logs
            formatted_transformed = json.dumps(transformed, indent=2, sort_keys=True, ensure_ascii=False)
            _logger.info("Data Jira yang telah ditransformasi: \n%s", formatted_transformed)
        except Exception as e:
            _logger.error("Error saat parsing data Jira: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error parsing Jira data: {str(e)}")
        
        try:
            user = transformed.get('reporter')
            domain_user = [('name', '=', user.get('display_name'))]
            domain_category = [('name', '=', 'Others')]
            project_id_val = transformed.get('project_id') or ""
            company_split = project_id_val.split('_')
            company_code = company_split[0]
            _logger.info("Company code: %s", company_code)


            match company_code:
                case 'ITMS':
                    domain_company = [('name', '=', 'IT Manage Service')]
                case 'CSD':
                    domain_company = [('name', '=', 'Custom Solution')]
                case 'SI':
                    domain_company = [('name', '=', 'System Integrator')]
                case _:
                    domain_company = [('name', '=', 'PT Bangunindo Teknusa Jaya')]

            _logger.info("Domain company: %s", domain_company)
            _logger.info("Domain user: %s", domain_user)
            _logger.info("Domain category: %s", domain_category)

            company = find_data('res.company', domain_company, ["id", "currency_id"])
            if not company:
                _logger.error("Company not found: %s", domain_company)
                raise HTTPException(status_code=404, detail="Company not found")
            company = company[0]

            user = find_data('hr.employee', domain_user, ["id", "name"])
            category = find_data('product.product', domain_category, ["id", "name"])
            if not category:
                _logger.error("Category not found: %s", domain_category)
                raise HTTPException(status_code=404, detail="Category not found")
            category = category[0]

            if user and len(user) > 0:
                user_id = user[0]['id']
            else:
                user_id = 1

            if transformed.get('issue_type') == "Invoice Payment":
                _logger.info("Membuat data vendor bill")
                existing_records = find_data('account.move',[('narration', '=', transformed.get('key'))],['id'])
                if existing_records and len(existing_records) > 0:
                    _logger.warning("Vendor Bill sudah ada")
                    return {"Status": "Vendor Bill Already Exists"}
                else:
                    data_vendor_bill = {
                        'move_type': 'in_invoice',
                        'narration': transformed.get('key'),
                        'invoice_line_ids': [(0, 0, {
                            'name': transformed.get('summary'),
                            'price_unit': transformed.get('total_payment'),
                        })]
                    }
                    record = create_data('account.move', data_vendor_bill)
                    _logger.info("Vendor Bill berhasil dibuat dengan id %s", record)
                    return {"Status": f"Vendor Bill Created With id {record}"}
            else:
                _logger.info("Membuat data expense")
                existing_records = find_data('hr.expense',[('name', '=', transformed.get('key'))],['id'])
                if existing_records and len(existing_records) > 0:
                    _logger.warning("Expense sudah ada")
                    return {"Status": "Expense Already Exists"}
                else:
                    data = {
                        "name": transformed.get('key'),
                        "product_id": category['id'],
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "total_amount_currency": transformed.get('total_payment'),
                        "price_unit": transformed.get('total_payment'),
                        "employee_id": user_id,
                        "company_id": company['id'],
                        "currency_id": company['currency_id'][0],
                        "description": transformed.get('summary')
                    }
                    record = create_data('hr.expense', data)
                    _logger.info("Expense berhasil dibuat dengan id %s", record)
                    return {"Status": f"Expense Created With id {record}"}
        except HTTPException:
            raise
        except Exception as e:
            _logger.error("Error saat memproses data expense: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error Creating Expense: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        _logger.error("Unexpected error in create_expense endpoint: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")