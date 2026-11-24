import os
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .. import models
from ..database import SessionLocal
from .email_reports import send_report

daily_report_scheduler = BackgroundScheduler()


def _daily_report_job() -> None:
    db = SessionLocal()
    try:
        settings = {row.key: row.value for row in db.query(models.AgencySetting).all()}
        recipient = settings.get("daily_report_recipient", os.getenv("DAILY_REPORT_RECIPIENT", ""))
        automation = db.query(models.AutomationJob).filter(models.AutomationJob.name == "daily_email").first()
        if settings.get("daily_report_enabled") != "true" or not recipient or not automation or not automation.enabled:
            return
        send_report(db, recipient)
    except Exception as exc:
        db.rollback()
        db.add(models.EmailReport(
            recipient="",
            subject="NEXUS Daily Agency Report",
            status="failed",
            detail=f"Scheduled report failed: {str(exc)[:900]}",
        ))
        db.commit()
    finally:
        db.close()


def configure_daily_report(time_value: str, timezone_name: str, enabled: bool) -> None:
    if not daily_report_scheduler.running:
        return
    job = daily_report_scheduler.get_job("daily_agency_report")
    if job:
        daily_report_scheduler.remove_job("daily_agency_report")
    if enabled:
        hour_text, minute_text = time_value.split(":", 1)
        timezone = ZoneInfo(timezone_name)
        daily_report_scheduler.add_job(
            _daily_report_job,
            CronTrigger(hour=int(hour_text), minute=int(minute_text), timezone=timezone),
            id="daily_agency_report",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )


def start_scheduler() -> None:
    if not daily_report_scheduler.running:
        daily_report_scheduler.start()
    db = SessionLocal()
    try:
        settings = {row.key: row.value for row in db.query(models.AgencySetting).all()}
    finally:
        db.close()
    configure_daily_report(
        settings.get("daily_report_time", "09:00"),
        settings.get("timezone", "Europe/Riga"),
        settings.get("daily_report_enabled") == "true",
    )


def stop_scheduler() -> None:
    if daily_report_scheduler.running:
        daily_report_scheduler.shutdown(wait=False)
