import json
import os
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from .. import models
from ..database import SessionLocal

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
HEADERS = ["Task ID", "Timestamp", "Assigned By", "Agent Name", "Task Description",
           "Priority", "Status", "Output / Result Link", "Completion Time"]


def _credentials() -> Credentials:
    raw = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if not raw:
        raise HTTPException(503, "Google Sheets is not configured. Set GOOGLE_SERVICE_ACCOUNT_JSON.")
    try:
        if raw.startswith("{"):
            info = json.loads(raw)
        else:
            info = json.loads(Path(raw).read_text(encoding="utf-8"))
        return Credentials.from_service_account_info(info, scopes=SCOPES)
    except (OSError, ValueError, TypeError) as exc:
        raise HTTPException(503, "Google service account configuration is invalid.") from exc


def _values_service():
    spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID", "").strip()
    if not spreadsheet_id:
        raise HTTPException(503, "Google Sheets is not configured. Set GOOGLE_SPREADSHEET_ID.")
    service = build("sheets", "v4", credentials=_credentials(), cache_discovery=False)
    return service.spreadsheets().values(), spreadsheet_id, os.getenv("GOOGLE_SHEET_TAB", "Tasks")


def sync_tasks(db: Session) -> dict[str, Any]:
    values, spreadsheet_id, tab = _values_service()
    escaped_tab = tab.replace("'", "''")
    quoted_range = f"'{escaped_tab}'!A:I"
    response = values.get(spreadsheetId=spreadsheet_id, range=quoted_range).execute()
    rows = response.get("values", [])
    if not rows or rows[0] != HEADERS:
        values.update(
            spreadsheetId=spreadsheet_id,
            range=f"'{escaped_tab}'!A1:I1",
            valueInputOption="RAW",
            body={"values": [HEADERS]},
        ).execute()
        rows = [HEADERS]
    row_by_key = {row[0]: index + 2 for index, row in enumerate(rows[1:]) if row}
    tasks = db.query(models.Task).order_by(models.Task.id).all()
    updates = []
    appended = []
    for task in tasks:
        result_link = f"/api/tasks/{task.id}" if task.deliverables else ""
        row = [
            task.task_key,
            task.created_at.isoformat(),
            "Alex Morgan",
            task.employee.name if task.employee else "",
            task.description,
            task.priority,
            task.status.value,
            result_link,
            task.completed_at.isoformat() if task.completed_at else "",
        ]
        if task.task_key in row_by_key:
            row_number = row_by_key[task.task_key]
            updates.append({"range": f"'{escaped_tab}'!A{row_number}:I{row_number}", "values": [row]})
        else:
            appended.append(row)
    if updates:
        values.batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"valueInputOption": "RAW", "data": updates},
        ).execute()
    if appended:
        values.append(
            spreadsheetId=spreadsheet_id,
            range=f"'{escaped_tab}'!A:I",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": appended},
        ).execute()
    return {"spreadsheet_id": spreadsheet_id, "synchronized": len(tasks), "updated": len(updates), "inserted": len(appended)}


def log_sync(db: Session, status: str, detail: str, task_id: int | None = None) -> None:
    db.add(models.GoogleSheetSyncLog(task_id=task_id, status=status, detail=detail))
    db.commit()


def background_sync_tasks() -> None:
    db = SessionLocal()
    try:
        setting = db.query(models.AutomationJob).filter(models.AutomationJob.name == "sheets_sync").first()
        if setting and not setting.enabled:
            log_sync(db, "skipped", "Automatic Google Sheets synchronization is disabled.")
            return
        result = sync_tasks(db)
        log_sync(db, "success", f"Updated {result['updated']}, inserted {result['inserted']} of {result['synchronized']} task rows.")
    except HTTPException as exc:
        log_sync(db, "not_configured" if exc.status_code == 503 else "failed", str(exc.detail))
    except Exception as exc:
        log_sync(db, "failed", f"Google Sheets synchronization failed: {str(exc)[:800]}")
    finally:
        db.close()
