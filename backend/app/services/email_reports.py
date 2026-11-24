import os
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models


def agency_report_content(db: Session) -> tuple[str, str, str]:
    now = datetime.now(timezone.utc)
    tasks = db.query(models.Task).all()
    projects = db.query(models.Project).all()
    completed_today = [
        task for task in tasks
        if task.status == models.TaskStatus.completed and task.completed_at
        and task.completed_at.date() == now.date()
    ]
    blocked = [task for task in tasks if task.status == models.TaskStatus.blocked]
    in_progress = [task for task in tasks if task.status == models.TaskStatus.in_progress]
    subject = f"NEXUS Daily Agency Report — {now.date().isoformat()}"
    lines = [
        "NEXUS AGENCY DAILY REPORT",
        f"Generated: {now.isoformat()}",
        "",
        f"Agency overview: {len(projects)} projects; {len(tasks)} tasks total.",
        f"Tasks completed today: {len(completed_today)}",
        f"Tasks in progress: {len(in_progress)}",
        f"Blocked tasks: {len(blocked)}",
        "",
        "PROJECT UPDATES",
    ]
    lines.extend(f"- {p.project_key} {p.name}: {p.progress:.0f}% ({p.status.value})" for p in projects)
    lines.extend(["", "BLOCKED TASKS"])
    lines.extend(f"- {task.task_key} {task.title}" for task in blocked)
    if not blocked:
        lines.append("- None")
    lines.extend(["", "NEXT STEPS", "- Review blocked items and pending specialist deliverables."])
    body = "\n".join(lines)
    return subject, body, f"<pre>{body.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')}</pre>"


def send_report(db: Session, recipient: str) -> models.EmailReport:
    host = os.getenv("SMTP_HOST", "").strip()
    username = os.getenv("SMTP_USERNAME", "").strip()
    password = os.getenv("SMTP_PASSWORD", "")
    sender = os.getenv("SMTP_FROM_EMAIL", username).strip()
    if not all((host, username, password, sender, recipient)):
        raise HTTPException(
            status_code=503,
            detail="Email reporting is not configured. Set SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL, and recipient.",
        )
    subject, body, html = agency_report_content(db)
    report = models.EmailReport(recipient=recipient, subject=subject, status="sending")
    db.add(report)
    db.commit()
    db.refresh(report)
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient
    message.set_content(body)
    message.add_alternative(html, subtype="html")
    try:
        with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587")), timeout=20) as smtp:
            smtp.starttls()
            smtp.login(username, password)
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException, ValueError) as exc:
        report.status = "failed"
        report.detail = str(exc)[:1000]
        db.commit()
        raise HTTPException(status_code=502, detail="Email provider did not confirm delivery.") from exc
    report.status = "sent"
    report.detail = "SMTP provider accepted the message."
    db.commit()
    return report
