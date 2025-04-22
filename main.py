import logging
import logging.handlers
from fastapi import FastAPI, HTTPException, Request, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from base_rpc import BaseRpc
from datetime import datetime
import json
import pandas as pd
import os
import time

import datetime as dt
from pydantic import BaseModel, Field

# Buat folder logs jika belum ada
os.environ['TZ'] = 'Asia/Jakarta'
time.tzset()

log_directory = "storage/logs"
os.makedirs(log_directory, exist_ok=True)

LOG_FILE = os.path.join(log_directory, "app.log")
file_handler = logging.handlers.TimedRotatingFileHandler(
    LOG_FILE, when="midnight", interval=1, backupCount=7, encoding="utf-8"
)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# Logger untuk modul ini
_logger = logging.getLogger(__name__)

app = FastAPI()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    if response.status_code == 200:
        _logger.info("Request: method=%s, path=%s, status_code=%s", request.method, request.url.path, response.status_code)
    else:
        _logger.error("Request: method=%s, path=%s, status_code=%s", request.method, request.url.path, response.status_code)
    return response

# ================================
# Definisi model Pydantic baru
# ================================

class StatusCategory(BaseModel):
    name: str

class Status(BaseModel):
    name: str
    status_category: StatusCategory = Field(alias="statusCategory")

class User(BaseModel):
    display_name: str = Field(alias="displayName")
    email: str | None = Field(alias="emailAddress", default=None)
    account_id: str = Field(alias="accountId")
    active: bool

class IssueType(BaseModel):
    name: str = Field(alias="namedValue")
    subtask: bool

class Fields(BaseModel):
    status: Status
    reporter: User | None = None
    issue_type: IssueType = Field(alias="issuetype")
    project: dict | None = None
    summary: str | None = None
    project_id: dict | None = Field(alias="customfield_10144")
    total_payment_entertainment: int | None = Field(alias="customfield_10041", default=0)
    total_payment_food_beverages: int | None = Field(alias="customfield_10036", default=0)
    total_payment_gas_toll_parking: int | None = Field(alias="customfield_10038", default=0)
    total_payment_office_supplies: int | None = Field(alias="customfield_10039", default=0)
    total_payment_online_transportation: int | None = Field(alias="customfield_10037", default=0)
    total_payment_tickets_accommodation: int | None = Field(alias="customfield_10040", default=0)
    total_payment_other_cost: int | None = Field(alias="customfield_10076", default=0)
    total_payment: int | None = Field(alias="customfield_10030", default=None)
    total_payment_words: str | None = Field(alias="customfield_10035", default=None)
    down_payment: int | None = Field(alias="customfield_10145", default=None)
    down_payment_words: str | None = Field(alias="customfield_10146", default=None)
    balance: int | None = Field(alias="customfield_10147", default=None)
    balance_words: str | None = Field(alias="customfield_10148", default=None)
    actual_expense: int | None = Field(alias="customfield_10042", default=None)
    actual_expense_words: str | None = Field(alias="customfield_10043", default=None)
    done_at: dt.datetime | None = Field(alias="customfield_10044", default=None)

class JiraRequest(BaseModel):
    self_: str = Field(alias="self")
    id: int
    key: str
    changelog: dict | None = None
    fields: Fields

# ====================================
# Fungsi–fungsi helper (RPC, dsb)
# ====================================

def get_client():
    host = 'bangunindo_web'
    port = 8069
    # database = 'Bangunindo_prod'
    database = 'Bangunindo_test'
    login = 'admin'
    password = 'odoo'

    try:
        rpc = BaseRpc()
        rpc.set_config(host, database, port)
        _logger.info("auth config: host=%s, database=%s, port=%s", host, database, port)
        rpc.set_auth(login, password)
        _logger.info("auth rpc: login=%s, password=%s", login, password)
        return rpc
    except (ConnectionError, ConnectionResetError) as e:
        _logger.error("Error dalam get_client: %s", e)
        raise

def find_data(model_name, domain, field):
    try:
        client = get_client()
        data = client.search_read(model_name, domain, field)
        _logger.info("Data ditemukan pada model %s: %s", model_name, data)
        return data
    except Exception as e:
        _logger.error("Error dalam find_data pada model %s: %s", model_name, e)

def create_data(model_name, values):
    try:
        client = get_client()
        record_id = client.create(model_name, values)
        _logger.info("Data dibuat pada model %s dengan id %s", model_name, record_id)
        return record_id
    except Exception as e:
        _logger.error("Error dalam create_data pada model %s: %s", model_name, e)

EXPECTED_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkppcmEgQVBJIFRva2VuIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

# ====================================
# Dependency untuk Bearer Token di Swagger
# ====================================
token_auth_scheme = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(token_auth_scheme)) -> str:
    if credentials.credentials != EXPECTED_TOKEN:
        _logger.warning("Token tidak valid: %s", credentials.credentials)
        raise HTTPException(status_code=403, detail="Invalid token")
    return credentials.credentials

@app.get("/test")
def test():
    try:
        _logger.info("Endpoint /test diakses")
        return {"message": "Hello, FastApi!"}
    except Exception as e:
        _logger.error("Error dalam test: %s", e)

@app.get("/")
def read_root():
    client = get_client()
    _logger.info("Endpoint root diakses, client: %s", client)
    return {"message": "Hello, FastApi !"}

# ====================================================
# Endpoint /jira/expenses dengan pemetaan data reporter yang eksplisit
# ====================================================

@app.post("/jira/expenses")
async def create_expense(payload: JiraRequest, request: Request, token: str = Depends(verify_token)):
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
            # domain_company = [('name', '=', 'PT Bangunindo Teknusa Jaya')]
            domain_user = [('name', '=', user.get('display_name'))]
            domain_category = [('name', '=', 'Others')]
            company_split = transformed.get('project_id').split('_')
            company_code = company_split[0]

            match company_code:
                case 'ITMS':
                    domain_company = [('name', '=', 'IT Manage Service')]
                case 'CSD':
                    domain_company = [('name', '=', 'Custom Solution')]
                case 'SI':
                    domain_company = [('name', '=', 'System Integrator')]
                case _:
                    domain_company = [('name', '=', 'PT Bangunindo Teknusa Jaya')]

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
                # Check if record exists
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

if __name__ == "__main__":
    import uvicorn
    _logger.info("Starting FastAPI server pada 127.0.0.1:8050")
    uvicorn.run(app, host="127.0.0.1", port=8050)
