import asyncio
import os
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import update
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import SessionLocal, get_db
from ..services.google_sheets import background_sync_tasks
from ..services.llm import execute_employee_task

router = APIRouter()


@router.get("")
def list_tasks(
    project_id: int | None = None,
    employee_id: int | None = None,
    status: models.TaskStatus | None = None,
    priority: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Task)
    if project_id is not None:
        query = query.filter(models.Task.project_id == project_id)
    if employee_id is not None:
        query = query.filter(models.Task.employee_id == employee_id)
    if status is not None:
        query = query.filter(models.Task.status == status)
    if priority:
        query = query.filter(models.Task.priority == priority)
    tasks = query.order_by(models.Task.created_at.desc()).limit(200).all()
    return [{
        "id": t.id, "task_key": t.task_key, "title": t.title, "description": t.description,
        "status": t.status.value, "priority": t.priority, "project": t.project.name,
        "project_key": t.project.project_key, "employee": t.employee.name if t.employee else None,
        "employee_id": t.employee_id, "started_at": t.started_at, "completed_at": t.completed_at,
        "error_detail": t.error_detail,
        "dependencies": [{"id": dep.id, "task_key": dep.task_key, "title": dep.title, "status": dep.status.value}
                         for link in db.query(models.TaskDependency).filter(models.TaskDependency.task_id == t.id)
                         for dep in [db.get(models.Task, link.depends_on_id)] if dep is not None],
    } for t in tasks]


@router.post("")
def create_task(payload: schemas.TaskCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    if payload.employee_id is not None and not db.get(models.Employee, payload.employee_id):
        raise HTTPException(404, "Assigned employee not found")
    if payload.priority not in {"low", "medium", "high", "urgent"}:
        raise HTTPException(422, "Priority must be low, medium, high, or urgent.")
    dependencies = []
    for dependency_id in set(payload.depends_on_ids):
        dependency = db.get(models.Task, dependency_id)
        if not dependency or dependency.project_id != project.id:
            raise HTTPException(422, "Task dependencies must exist in the same project.")
        dependencies.append(dependency)
    task = models.Task(
        task_key=f"{project.project_key}-T{uuid4().hex[:6].upper()}",
        title=payload.title,
        description=payload.description,
        project_id=payload.project_id,
        employee_id=payload.employee_id,
        priority=payload.priority,
    )
    db.add(task)
    db.flush()
    for dependency in dependencies:
        db.add(models.TaskDependency(task_id=task.id, depends_on_id=dependency.id))
    db.add(models.ActivityLog(type="task_assigned", title=f"Task assigned: {task.title}",
                              detail="A new task entered the agency workflow.", project_id=project.id,
                              employee_id=task.employee_id))
    db.commit()
    background_tasks.add_task(background_sync_tasks)
    return {"id": task.id, "task_key": task.task_key, "status": task.status.value}


@router.get("/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(models.Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    dependencies = db.query(models.TaskDependency).filter(models.TaskDependency.task_id == task_id).all()
    return {
        "id": task.id, "task_key": task.task_key, "title": task.title, "description": task.description,
        "status": task.status.value, "priority": task.priority, "employee": task.employee.name if task.employee else None,
        "project": task.project.name, "input_context": task.input_context,
        "deliverables": [{"title": d.title, "content": d.content, "created_at": d.created_at} for d in task.deliverables],
        "executions": [{"id": ex.id, "status": ex.status, "summary": ex.summary, "error_detail": ex.error_detail,
                        "started_at": ex.started_at, "completed_at": ex.completed_at} for ex in task.executions],
        "dependencies": [{"id": db.get(models.Task, link.depends_on_id).id,
                          "task_key": db.get(models.Task, link.depends_on_id).task_key,
                          "status": db.get(models.Task, link.depends_on_id).status.value}
                         for link in dependencies if db.get(models.Task, link.depends_on_id)],
        "created_at": task.created_at, "started_at": task.started_at, "completed_at": task.completed_at,
        "error_detail": task.error_detail,
    }


@router.patch("/{task_id}")
def update_task(task_id: int, background_tasks: BackgroundTasks, status: models.TaskStatus | None = None,
                employee_id: int | None = None,
                db: Session = Depends(get_db)):
    task = db.get(models.Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if status is None and employee_id is None:
        raise HTTPException(422, "Provide a new status or assigned employee.")
    if employee_id is not None and not db.get(models.Employee, employee_id):
        raise HTTPException(404, "Assigned employee not found.")
    if status == models.TaskStatus.completed and not task.deliverables:
        raise HTTPException(409, "A task cannot be completed without a persisted deliverable.")
    if task.status == models.TaskStatus.completed and status not in (None, models.TaskStatus.completed):
        raise HTTPException(409, "Completed tasks cannot be reopened; use a new revision task.")
    if employee_id is not None:
        task.employee_id = employee_id
    if status is not None:
        task.status = status
    if status == models.TaskStatus.completed:
        task.completed_at = datetime.now(timezone.utc)
    if status == models.TaskStatus.queued:
        task.error_detail = None
    db.add(models.ActivityLog(type="task_status_changed", title=f"Task status changed: {task.title}",
                              detail=f"Status set to {status.value if status else task.status.value}.", project_id=task.project_id,
                              employee_id=task.employee_id))
    db.commit()
    background_tasks.add_task(background_sync_tasks)
    return {"id": task.id, "status": task.status.value}


def _run_execution(execution_id: int, task_id: int) -> None:
    db = SessionLocal()
    try:
        execution = db.get(models.TaskExecution, execution_id)
        task = db.get(models.Task, task_id)
        if not execution or not task or not task.employee:
            return
        execution.status = "running"
        db.commit()
        try:
            output = asyncio.run(execute_employee_task(task.employee, task, task.project))
            for item in output["deliverables"]:
                db.add(models.Deliverable(task_id=task.id, title=item.title, content=item.content))
            db.flush()
            if not db.query(models.Deliverable).filter(models.Deliverable.task_id == task.id).count():
                raise ValueError("Agent returned no persisted deliverable.")
            execution.status = "completed"
            execution.summary = output["summary"]
            execution.payload = output
            execution.completed_at = datetime.now(timezone.utc)
            task.status = models.TaskStatus.completed
            task.completed_at = datetime.now(timezone.utc)
            task.error_detail = None
            task.employee.status = "idle"
            finished_count = sum(t.status == models.TaskStatus.completed for t in task.project.tasks)
            task.project.progress = round(finished_count / max(len(task.project.tasks), 1) * 100)
            if task.project.tasks and all(item.status == models.TaskStatus.completed for item in task.project.tasks):
                task.project.status = models.ProjectStatus.completed
            db.add(models.ActivityLog(type="deliverable_submitted", title=f"Deliverable submitted: {task.title}",
                                      detail=output["summary"], project_id=task.project_id, employee_id=task.employee_id))
            db.add(models.TeamMessage(sender_employee_id=task.employee_id, project_id=task.project_id,
                                      task_id=task.id, message=output["handover_notes"] or output["summary"]))
            db.commit()
        except Exception as exc:
            db.rollback()
            execution = db.get(models.TaskExecution, execution_id)
            task = db.get(models.Task, task_id)
            if execution and task:
                execution.status = "failed"
                execution.error_detail = str(exc)[:2000]
                execution.completed_at = datetime.now(timezone.utc)
                task.status = models.TaskStatus.blocked
                task.error_detail = str(exc)[:2000]
                if task.employee:
                    task.employee.status = "blocked"
                db.add(models.ActivityLog(type="agent_execution_failed", title=f"Execution failed: {task.title}",
                                          detail=str(exc)[:1000], project_id=task.project_id,
                                          employee_id=task.employee_id))
                db.commit()
        background_sync_tasks()
    finally:
        db.close()


@router.post("/{task_id}/execute", status_code=202)
def execute_task(task_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if not os.getenv("OPENAI_API_KEY", "").strip():
        raise HTTPException(503, "AI execution is not configured. Set OPENAI_API_KEY and restart the backend.")
    task = db.get(models.Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if not task.employee:
        raise HTTPException(409, "Task has no assigned employee.")
    if task.status == models.TaskStatus.completed:
        raise HTTPException(409, "Task is already complete.")
    if task.status == models.TaskStatus.in_progress:
        raise HTTPException(409, "Task execution is already in progress.")
    if task.status == models.TaskStatus.cancelled:
        raise HTTPException(409, "Cancelled tasks cannot be executed.")
    if task.project.status != models.ProjectStatus.active:
        raise HTTPException(409, "The project must be active before a task can execute.")
    links = db.query(models.TaskDependency).filter(models.TaskDependency.task_id == task.id).all()
    unfinished = [db.get(models.Task, link.depends_on_id) for link in links]
    unfinished = [dependency for dependency in unfinished if dependency and dependency.status != models.TaskStatus.completed]
    if unfinished:
        raise HTTPException(409, {"message": "Task dependencies are not complete.", "dependencies": [d.task_key for d in unfinished]})
    claimed = db.execute(
        update(models.Task)
        .where(
            models.Task.id == task.id,
            models.Task.status.in_([models.TaskStatus.queued, models.TaskStatus.blocked]),
        )
        .values(status=models.TaskStatus.in_progress, started_at=datetime.now(timezone.utc), error_detail=None)
    )
    if claimed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Task status changed; reload before executing.")
    db.refresh(task)
    execution = models.TaskExecution(task_id=task.id, employee_id=task.employee_id, status="queued", summary="")
    db.add(execution)
    db.flush()
    task.employee.status = "working"
    db.add(models.ActivityLog(type="agent_started", title=f"Agent started: {task.title}",
                              detail=f"{task.employee.name} began task execution.", project_id=task.project_id,
                              employee_id=task.employee_id))
    db.commit()
    background_tasks.add_task(_run_execution, execution.id, task.id)
    return {"task_id": task.id, "execution_id": execution.id, "status": "queued"}


@router.post("/{task_id}/retry", status_code=202)
def retry_task(task_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    task = db.get(models.Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if task.status != models.TaskStatus.blocked:
        raise HTTPException(409, "Only blocked tasks can be retried.")
    if not os.getenv("OPENAI_API_KEY", "").strip():
        raise HTTPException(503, "AI execution is not configured. Set OPENAI_API_KEY and restart the backend.")
    task.status = models.TaskStatus.queued
    task.error_detail = None
    db.commit()
    return execute_task(task_id, background_tasks, db)
