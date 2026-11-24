from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..schemas import ChatRequest
from ..services.llm import chat_with_employee

router = APIRouter()


@router.post("/project-manager/chat")
async def project_manager_chat(payload: ChatRequest, db: Session = Depends(get_db)):
    manager = db.query(models.Employee).filter(models.Employee.employee_key == "alex").first()
    if not manager:
        raise HTTPException(503, "Project Manager profile is unavailable.")
    projects = db.query(models.Project).order_by(models.Project.updated_at.desc()).limit(30).all()
    tasks = db.query(models.Task).order_by(models.Task.created_at.desc()).limit(100).all()
    context = {
        "projects": [{"key": p.project_key, "name": p.name, "status": p.status.value, "progress": p.progress}
                     for p in projects],
        "tasks": [{"key": t.task_key, "title": t.title, "status": t.status.value,
                   "employee": t.employee.name if t.employee else None,
                   "deliverables": [d.title for d in t.deliverables]} for t in tasks],
    }
    history_rows = db.query(models.ChatMessage).filter(
        models.ChatMessage.employee_id == manager.id
    ).order_by(models.ChatMessage.created_at.desc()).limit(12).all()
    history = [
        {"role": "assistant" if item.sender == manager.name else "user", "content": item.message}
        for item in reversed(history_rows)
    ]
    reply = await chat_with_employee(manager, payload.message, context, history)
    db.add(models.ChatMessage(employee_id=manager.id, sender="Boss", receiver=manager.name, message=payload.message))
    db.add(models.ChatMessage(employee_id=manager.id, sender=manager.name, receiver="Boss", message=reply))
    db.commit()
    return {"reply": reply}
