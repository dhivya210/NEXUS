from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db

router = APIRouter()
AUTOMATION_JOBS = {
    "project_workflow": ("Project workflow", "Creates specialist tasks and manages project stages."),
    "task_assignment": ("Task assignment", "Routes work to the selected specialist."),
    "qa_feedback": ("QA feedback", "Tracks QA findings and developer revisions."),
    "sheets_sync": ("Google Sheets synchronization", "Synchronizes task ledger with the configured spreadsheet."),
    "daily_email": ("Daily email report", "Sends scheduled daily agency report."),
}
MUTABLE_AUTOMATIONS = {"sheets_sync", "daily_email"}


class AutomationUpdate(BaseModel):
    enabled: bool


@router.get("")
def list_automations(db: Session = Depends(get_db)):
    records = {job.name: job for job in db.query(models.AutomationJob).all()}
    return [{
        "key": key,
        "name": label,
        "description": description,
        "enabled": records[key].enabled if key in records else key in {"project_workflow", "task_assignment", "qa_feedback"},
        "mutable": key in MUTABLE_AUTOMATIONS,
        "last_status": records[key].last_status if key in records else "ready",
        "last_run_at": records[key].last_run_at if key in records else None,
        "detail": records[key].detail if key in records else "",
    } for key, (label, description) in AUTOMATION_JOBS.items()]


@router.patch("/{key}")
def update_automation(key: str, payload: AutomationUpdate, db: Session = Depends(get_db)):
    if key not in AUTOMATION_JOBS:
        raise HTTPException(404, "Automation not found.")
    if key not in MUTABLE_AUTOMATIONS:
        raise HTTPException(409, "This core workflow is controlled by the delivery system.")
    record = db.query(models.AutomationJob).filter(models.AutomationJob.name == key).first()
    if not record:
        record = models.AutomationJob(name=key, enabled=payload.enabled, last_status="configured")
        db.add(record)
    else:
        record.enabled = payload.enabled
        record.last_status = "enabled" if payload.enabled else "disabled"
    db.commit()
    return {"key": key, "enabled": record.enabled, "status": record.last_status}
