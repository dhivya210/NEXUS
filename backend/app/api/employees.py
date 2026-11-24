from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from ..schemas import ChatRequest
from ..agents import EMPLOYEES
from ..services.llm import chat_with_employee

router = APIRouter()


@router.get("")
def list_employees(db: Session = Depends(get_db)):
    employees = db.query(models.Employee).all()
    return [{"id": e.id, "employee_key": e.employee_key, "name": e.name, "title": e.title,
             "initials": e.initials, "description": e.description, "status": e.status,
             "responsibilities": e.responsibilities,
             "completed_tasks": sum(t.status == models.TaskStatus.completed for t in e.tasks),
             "pending_tasks": sum(t.status in (models.TaskStatus.queued, models.TaskStatus.in_progress) for t in e.tasks),
             "blocked_tasks": sum(t.status == models.TaskStatus.blocked for t in e.tasks),
             "current_assignment": next((t.title for t in e.tasks if t.status == models.TaskStatus.in_progress), None)}
            for e in employees]


@router.get("/{employee_id}")
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    e = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not e:
        raise HTTPException(404, "Employee not found")
    profile = next((p for p in EMPLOYEES if p["key"] == e.employee_key), {})
    return {"id": e.id, "employee_key": e.employee_key, "name": e.name, "title": e.title,
            "initials": e.initials, "description": e.description, "status": e.status,
            "responsibilities": e.responsibilities, "system_prompt": profile.get("prompt", e.system_prompt),
            "tasks": [{"id": t.id, "task_key": t.task_key, "title": t.title, "status": t.status.value}
                      for t in e.tasks]}


@router.get("/{employee_id}/tasks")
def employee_tasks(employee_id: int, db: Session = Depends(get_db)):
    e = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not e:
        raise HTTPException(404, "Employee not found")
    return [{"id": t.id, "title": t.title, "status": t.status.value, "project": t.project.name} for t in e.tasks]


@router.get("/{employee_id}/performance")
def employee_performance(employee_id: int, db: Session = Depends(get_db)):
    employee = db.get(models.Employee, employee_id)
    if not employee:
        raise HTTPException(404, "Employee not found")
    completed = [task for task in employee.tasks if task.status == models.TaskStatus.completed]
    durations = [
        (task.completed_at - task.started_at).total_seconds() / 3600
        for task in completed if task.completed_at and task.started_at
    ]
    return {
        "employee_id": employee.id,
        "name": employee.name,
        "assigned": len(employee.tasks),
        "completed": len(completed),
        "pending": sum(task.status in (models.TaskStatus.queued, models.TaskStatus.in_progress) for task in employee.tasks),
        "blocked": sum(task.status == models.TaskStatus.blocked for task in employee.tasks),
        "average_completion_hours": round(sum(durations) / len(durations), 2) if durations else None,
        "completion_rate": round(len(completed) / len(employee.tasks) * 100, 1) if employee.tasks else None,
        "tasks": [{"task_key": task.task_key, "title": task.title, "status": task.status.value}
                  for task in employee.tasks],
    }


@router.get("/{employee_id}/chat")
def employee_chat_history(employee_id: int, db: Session = Depends(get_db)):
    employee = db.get(models.Employee, employee_id)
    if not employee:
        raise HTTPException(404, "Employee not found")
    messages = db.query(models.ChatMessage).filter(
        models.ChatMessage.employee_id == employee_id
    ).order_by(models.ChatMessage.created_at.asc()).limit(100).all()
    return [{"sender": message.sender, "message": message.message, "created_at": message.created_at}
            for message in messages]


@router.post("/{employee_id}/chat")
async def employee_chat(employee_id: int, payload: ChatRequest, db: Session = Depends(get_db)):
    e = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not e:
        raise HTTPException(404, "Employee not found")
    previous = db.query(models.ChatMessage).filter(
        models.ChatMessage.employee_id == e.id
    ).order_by(models.ChatMessage.created_at.desc()).limit(12).all()
    history = [
        {"role": "assistant" if message.sender == e.name else "user", "content": message.message}
        for message in reversed(previous)
    ]
    context = {
        "employee": {"name": e.name, "role": e.title, "status": e.status},
        "assigned_tasks": [
            {"key": task.task_key, "title": task.title, "status": task.status.value,
             "project": task.project.name, "deliverables": [d.title for d in task.deliverables]}
            for task in e.tasks
        ],
    }
    reply = await chat_with_employee(e, payload.message, context, history)
    db.add(models.ChatMessage(employee_id=e.id, sender="Boss", receiver=e.name, message=payload.message))
    db.add(models.ChatMessage(employee_id=e.id, sender=e.name, receiver="Boss", message=reply))
    db.commit()
    return {"reply": reply}
