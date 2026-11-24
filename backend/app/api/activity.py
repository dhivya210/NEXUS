from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models

router = APIRouter()


@router.get("")
def activity(db: Session = Depends(get_db)):
    logs = db.query(models.ActivityLog).order_by(models.ActivityLog.created_at.desc()).limit(50).all()
    return [{"id": l.id, "type": l.type, "title": l.title, "detail": l.detail, "created_at": l.created_at}
            for l in logs]
