from datetime import datetime
import re
from pydantic import BaseModel, Field, field_validator


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: str = Field(min_length=4)
    client_name: str
    client_email: str = ""
    priority: str = "medium"
    deadline: datetime | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None


class TaskCreate(BaseModel):
    title: str
    description: str
    project_id: int
    employee_id: int | None = None
    priority: str = "medium"
    depends_on_ids: list[int] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class EmailSendRequest(BaseModel):
    recipient: str | None = None

    @field_validator("recipient")
    @classmethod
    def validate_recipient(cls, value: str | None) -> str | None:
        if value and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("Recipient must be a valid email address.")
        return value


class SettingsUpdate(BaseModel):
    agency_name: str = Field(min_length=2, max_length=100)
    daily_report_recipient: str = ""
    daily_report_enabled: bool = False
    daily_report_time: str = Field(default="09:00", pattern=r"^\d{2}:\d{2}$")
    timezone: str = "Europe/Riga"

    @field_validator("daily_report_time")
    @classmethod
    def validate_report_time(cls, value: str) -> str:
        datetime.strptime(value, "%H:%M")
        return value

    @field_validator("daily_report_recipient")
    @classmethod
    def validate_report_recipient(cls, value: str) -> str:
        if value and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("Report recipient must be a valid email address.")
        return value
