from pydantic import BaseModel, Field
import datetime as dt

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
