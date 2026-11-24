import csv
import io
import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas
from ..services.email_reports import send_report

router = APIRouter()


@router.get("/agency")
def agency_report(db: Session = Depends(get_db)):
    tasks = db.query(models.Task).all()
    projects = db.query(models.Project).all()
    employees = db.query(models.Employee).all()
    completed = [t for t in tasks if t.status == models.TaskStatus.completed]
    today = datetime.now(timezone.utc).date()
    completed_today = sum(t.completed_at is not None and t.completed_at.date() == today for t in completed)
    status_counts = {status.value: sum(t.status.value == status.value for t in tasks)
                     for status in models.TaskStatus}
    employee_counts = [{"name": e.name, "completed": sum(t.status == models.TaskStatus.completed for t in e.tasks),
                        "active": sum(t.status in (models.TaskStatus.queued, models.TaskStatus.in_progress) for t in e.tasks)}
                       for e in employees]
    finished_durations = [
        (t.completed_at - t.started_at).total_seconds() / 3600
        for t in completed if t.started_at and t.completed_at
    ]
    test_runs = db.query(models.TestExecution).all()
    deployments = db.query(models.Deployment).all()
    return {
        "total_tasks": len(tasks), "completed_tasks": len(completed), "completed_today": completed_today,
        "in_progress": status_counts["in_progress"], "blocked": status_counts["blocked"],
        "projects": len(projects), "delivered_projects": sum(p.status == models.ProjectStatus.completed for p in projects),
        "status_distribution": status_counts, "employee_distribution": employee_counts,
        "average_completion_hours": round(sum(finished_durations) / len(finished_durations), 2) if finished_durations else None,
        "qa_pass_rate": round(sum(test.status == "passed" for test in test_runs) / len(test_runs) * 100, 1) if test_runs else None,
        "qa_tests_executed": len(test_runs),
        "deployment_success_rate": round(sum(d.status == "succeeded" for d in deployments) / len(deployments) * 100, 1) if deployments else None,
        "deployments_recorded": len(deployments),
    }


@router.get("/employees")
def employee_reports(db: Session = Depends(get_db)):
    return [{
        "id": e.id, "name": e.name, "title": e.title,
        "assigned": len(e.tasks),
        "completed": sum(t.status == models.TaskStatus.completed for t in e.tasks),
        "pending": sum(t.status in (models.TaskStatus.queued, models.TaskStatus.in_progress) for t in e.tasks),
        "blocked": sum(t.status == models.TaskStatus.blocked for t in e.tasks)
    } for e in db.query(models.Employee).all()]


@router.get("/projects")
def project_reports(db: Session = Depends(get_db)):
    return [{"id": p.id, "project_key": p.project_key, "name": p.name, "client": p.client.name if p.client else "",
             "total_tasks": len(p.tasks), "completed_tasks": sum(t.status == models.TaskStatus.completed for t in p.tasks),
             "progress": p.progress, "status": p.status.value} for p in db.query(models.Project).all()]


@router.get("/trends")
def report_trends(db: Session = Depends(get_db)):
    from collections import defaultdict
    counts = defaultdict(int)
    tasks = db.query(models.Task).filter(models.Task.completed_at.is_not(None)).all()
    for task in tasks:
        counts[task.completed_at.date().isoformat()] += 1
    return [{"date": date, "completed": count} for date, count in sorted(counts.items())[-30:]]


@router.get("/export")
def export_projects(db: Session = Depends(get_db)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Project ID", "Project", "Client", "Status", "Priority", "Progress", "Total Tasks", "Completed Tasks"])
    for project in db.query(models.Project).order_by(models.Project.created_at.desc()):
        writer.writerow([
            project.project_key, project.name, project.client.name if project.client else "",
            project.status.value, project.priority, project.progress, len(project.tasks),
            sum(task.status == models.TaskStatus.completed for task in project.tasks),
        ])
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="nexus-projects.csv"'},
    )


@router.post("/email/send")
def send_email_report(payload: schemas.EmailSendRequest, db: Session = Depends(get_db)):
    recipient = payload.recipient or os.getenv("DAILY_REPORT_RECIPIENT", "")
    report = send_report(db, recipient)
    return {"id": report.id, "status": report.status, "recipient": report.recipient, "subject": report.subject}


@router.get("/email/history")
def email_history(db: Session = Depends(get_db)):
    return [{"id": report.id, "recipient": report.recipient, "subject": report.subject,
             "status": report.status, "detail": report.detail, "created_at": report.created_at}
            for report in db.query(models.EmailReport).order_by(models.EmailReport.created_at.desc()).limit(100)]
