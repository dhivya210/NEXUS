from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services.scheduler import configure_daily_report

router = APIRouter()

DEFAULTS = {
    "agency_name": "NEXUS",
    "daily_report_recipient": "",
    "daily_report_enabled": "false",
    "daily_report_time": "09:00",
    "timezone": "Europe/Riga",
}


@router.get("")
def get_settings(db: Session = Depends(get_db)):
    settings = DEFAULTS | {setting.key: setting.value for setting in db.query(models.AgencySetting).all()}
    settings["daily_report_enabled"] = settings["daily_report_enabled"] == "true"
    return settings


@router.put("")
def update_settings(payload: schemas.SettingsUpdate, db: Session = Depends(get_db)):
    try:
        ZoneInfo(payload.timezone)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(422, "Unknown time zone.") from exc
    values = payload.model_dump()
    values["daily_report_enabled"] = str(payload.daily_report_enabled).lower()
    for key, value in values.items():
        setting = db.get(models.AgencySetting, key)
        if setting:
            setting.value = str(value)
        else:
            db.add(models.AgencySetting(key=key, value=str(value)))
    db.commit()
    configure_daily_report(payload.daily_report_time, payload.timezone, payload.daily_report_enabled)
    return get_settings(db)
