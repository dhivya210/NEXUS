import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from ..services.google_sheets import background_sync_tasks, log_sync, sync_tasks

router = APIRouter()


@router.get("")
def integrations(db: Session = Depends(get_db)):
    last_sync = db.query(models.GoogleSheetSyncLog).order_by(models.GoogleSheetSyncLog.created_at.desc()).first()
    last_email = db.query(models.EmailReport).order_by(models.EmailReport.created_at.desc()).first()
    sheets_configured = bool(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON") and os.getenv("GOOGLE_SPREADSHEET_ID"))
    email_configured = all(os.getenv(key) for key in ("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM_EMAIL"))
    return [
        {"name": "OpenAI", "type": "openai", "configured": bool(os.getenv("OPENAI_API_KEY")),
         "connected": False, "description": "Role-specific task execution and grounded employee chat.",
         "last_sync": None, "error": "" if os.getenv("OPENAI_API_KEY") else "OPENAI_API_KEY is not configured"},
        {"name": "Google Sheets", "type": "google_sheets", "configured": sheets_configured,
         "connected": bool(last_sync and last_sync.status == "success"),
         "description": "Synchronize project tasks and status changes.",
         "last_sync": last_sync.created_at if last_sync and last_sync.status == "success" else None,
         "error": last_sync.detail if last_sync and last_sync.status != "success" else ""},
        {"name": "Email Delivery", "type": "email", "configured": email_configured,
         "connected": bool(last_email and last_email.status == "sent"),
         "description": "Send agency reports using SMTP.", "last_sync": None,
         "error": last_email.detail if last_email and last_email.status != "sent" else
         ("SMTP credentials not configured" if not email_configured else "")},
    ]


@router.post("/google-sheets/sync")
def sheets_sync(db: Session = Depends(get_db)):
    try:
        result = sync_tasks(db)
    except HTTPException as exc:
        log_sync(db, "failed", str(exc.detail))
        raise
    except Exception as exc:
        log_sync(db, "failed", f"Google Sheets synchronization failed: {str(exc)[:800]}")
        raise HTTPException(502, "Google Sheets synchronization failed; see integration logs.") from exc
    log_sync(db, "success", f"Updated {result['updated']}, inserted {result['inserted']} of {result['synchronized']} task rows.")
    return {"status": "synchronized", **result}


@router.get("/google-sheets/status")
def sheets_status(db: Session = Depends(get_db)):
    last = db.query(models.GoogleSheetSyncLog).order_by(models.GoogleSheetSyncLog.created_at.desc()).first()
    configured = bool(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON") and os.getenv("GOOGLE_SPREADSHEET_ID"))
    return {"connected": configured, "spreadsheet_id": os.getenv("GOOGLE_SPREADSHEET_ID") if configured else None,
            "last_sync": last.created_at if last and last.status == "success" else None,
            "error": last.detail if last and last.status == "failed" else ("" if configured else "Google service account and spreadsheet ID are required.")}
