from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db

router = APIRouter()


class TeamMessageCreate(BaseModel):
    receiver_employee_id: int | None = None
    project_id: int | None = None
    task_id: int | None = None
    message: str = Field(min_length=1, max_length=4000)


@router.get("/messages")
def list_messages(project_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(models.TeamMessage)
    if project_id is not None:
        query = query.filter(models.TeamMessage.project_id == project_id)
    messages = query.order_by(models.TeamMessage.created_at.desc()).limit(100).all()
    return [{
        "id": message.id,
        "sender": db.get(models.Employee, message.sender_employee_id).name if message.sender_employee_id else "Boss",
        "receiver": db.get(models.Employee, message.receiver_employee_id).name if message.receiver_employee_id else "Team",
        "project_id": message.project_id,
        "task_id": message.task_id,
        "message": message.message,
        "created_at": message.created_at,
    } for message in reversed(messages)]


@router.post("/messages")
def send_message(payload: TeamMessageCreate, db: Session = Depends(get_db)):
    if payload.receiver_employee_id and not db.get(models.Employee, payload.receiver_employee_id):
        raise HTTPException(404, "Receiver employee not found.")
    if payload.project_id and not db.get(models.Project, payload.project_id):
        raise HTTPException(404, "Project not found.")
    if payload.task_id:
        task = db.get(models.Task, payload.task_id)
        if not task:
            raise HTTPException(404, "Task not found.")
        if payload.project_id and task.project_id != payload.project_id:
            raise HTTPException(422, "Task does not belong to the selected project.")
    message = models.TeamMessage(
        receiver_employee_id=payload.receiver_employee_id,
        project_id=payload.project_id,
        task_id=payload.task_id,
        message=payload.message,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return {"id": message.id, "message": message.message, "created_at": message.created_at}
