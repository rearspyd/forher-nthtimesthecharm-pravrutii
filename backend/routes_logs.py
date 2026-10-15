import uuid
from datetime import date, datetime, timezone, timedelta
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from auth import get_current_user
from db import db, NO_ID, now_iso, audit
from cycles import estimate

router = APIRouter(tags=["logs"])
RECOVERY_DAYS = 30

FLOWS = Literal["none", "spotting", "light", "medium", "heavy"]


class DayLogIn(BaseModel):
    period: bool = False
    flow: FLOWS = "none"
    moods: list[str] = Field(default_factory=list, max_length=12)
    symptoms: list[str] = Field(default_factory=list, max_length=30)
    medications_taken: list[str] = Field(default_factory=list, max_length=30)
    notes: str = Field(default="", max_length=2000)
    base_version: Optional[int] = None
    force: bool = False


class MedicationIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    dose: str = Field(default="", max_length=120)
    schedule: str = Field(default="", max_length=200)
    active: bool = True


class ReminderIn(BaseModel):
    label: str = Field(min_length=1, max_length=120)
    kind: Literal["medication", "period", "custom"] = "custom"
    time: str = Field(pattern=r"^\d{2}:\d{2}$")
    days: list[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4, 5, 6])
    date: Optional[str] = None
    active: bool = True


def _valid_date(d: str) -> str:
    try:
        return date.fromisoformat(d).isoformat()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date, expected YYYY-MM-DD")


async def _purge_expired(user_id: str):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=RECOVERY_DAYS)).isoformat()
    for coll in (db.day_logs, db.medications, db.reminders):
        await coll.delete_many({"user_id": user_id, "deleted_at": {"$ne": None, "$lt": cutoff}})


@router.get("/logs")
async def list_logs(from_: str = Query(alias="from"), to: str = Query(), user=Depends(get_current_user)):
    _valid_date(from_); _valid_date(to)
    items = await db.day_logs.find({"user_id": user["user_id"], "date": {"$gte": from_, "$lte": to}, "deleted_at": None}, NO_ID).sort("date", 1).to_list(400)
    return items


@router.get("/logs/{day}")
async def get_log(day: str, user=Depends(get_current_user)):
    doc = await db.day_logs.find_one({"user_id": user["user_id"], "date": _valid_date(day), "deleted_at": None}, NO_ID)
    return doc or {"date": day, "exists": False}


@router.put("/logs/{day}")
async def upsert_log(day: str, body: DayLogIn, user=Depends(get_current_user)):
    day = _valid_date(day)
    existing = await db.day_logs.find_one({"user_id": user["user_id"], "date": day, "deleted_at": None}, NO_ID)
    if existing and body.base_version is not None and existing["version"] != body.base_version and not body.force:
        raise HTTPException(status_code=409, detail={"message": "This day was changed on another device.", "server": existing})
    data = body.model_dump(exclude={"base_version", "force"})
    if existing:
        doc = {**existing, **data, "version": existing["version"] + 1, "updated_at": now_iso()}
        await db.day_logs.replace_one({"id": existing["id"]}, doc)
    else:
        doc = {"id": str(uuid.uuid4()), "user_id": user["user_id"], "date": day, **data, "version": 1,
               "created_at": now_iso(), "updated_at": now_iso(), "deleted_at": None}
        await db.day_logs.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.delete("/logs/{day}")
async def delete_log(day: str, user=Depends(get_current_user)):
    res = await db.day_logs.update_one({"user_id": user["user_id"], "date": _valid_date(day), "deleted_at": None}, {"$set": {"deleted_at": now_iso()}})
    if not res.matched_count:
        raise HTTPException(status_code=404, detail="No log for that day")
    await audit(user["user_id"], "log_soft_deleted", {"date": day})
    return {"ok": True, "recoverable_days": RECOVERY_DAYS}


@router.get("/trash")
async def list_trash(user=Depends(get_current_user)):
    await _purge_expired(user["user_id"])
    q = {"user_id": user["user_id"], "deleted_at": {"$ne": None}}
    return {
        "logs": await db.day_logs.find(q, NO_ID).to_list(200),
        "medications": await db.medications.find(q, NO_ID).to_list(200),
        "reminders": await db.reminders.find(q, NO_ID).to_list(200),
        "recovery_days": RECOVERY_DAYS,
    }


@router.post("/trash/{kind}/{item_id}/restore")
async def restore(kind: Literal["logs", "medications", "reminders"], item_id: str, user=Depends(get_current_user)):
    coll = {"logs": db.day_logs, "medications": db.medications, "reminders": db.reminders}[kind]
    res = await coll.update_one({"user_id": user["user_id"], "id": item_id}, {"$set": {"deleted_at": None}})
    if not res.matched_count:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"ok": True}


@router.get("/cycles/estimate")
async def cycle_estimate(user=Depends(get_current_user)):
    logs = await db.day_logs.find({"user_id": user["user_id"], "period": True, "deleted_at": None}, {"_id": 0, "date": 1}).to_list(2000)
    return estimate([l["date"] for l in logs], user.get("settings", {}).get("cycle_context", "unknown"))


@router.get("/cycles/history")
async def cycles_history(user=Depends(get_current_user)):
    from reports import cycle_history
    logs = await db.day_logs.find({"user_id": user["user_id"], "period": True, "deleted_at": None}, {"_id": 0, "date": 1}).to_list(2000)
    return cycle_history([l["date"] for l in logs])


@router.get("/medications")
async def list_meds(user=Depends(get_current_user)):
    items = await db.medications.find({"user_id": user["user_id"], "deleted_at": None}, NO_ID).sort("created_at", 1).to_list(200)
    return items


@router.post("/medications", status_code=201)
async def create_med(body: MedicationIn, user=Depends(get_current_user)):
    doc = {"id": str(uuid.uuid4()), "user_id": user["user_id"], **body.model_dump(), "created_at": now_iso(), "deleted_at": None}
    await db.medications.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.put("/medications/{med_id}")
async def update_med(med_id: str, body: MedicationIn, user=Depends(get_current_user)):
    res = await db.medications.update_one({"id": med_id, "user_id": user["user_id"]}, {"$set": body.model_dump()})
    if not res.matched_count:
        raise HTTPException(status_code=404, detail="Medication not found")
    updated = await db.medications.find_one({"id": med_id}, NO_ID)
    return updated


@router.delete("/medications/{med_id}")
async def delete_med(med_id: str, user=Depends(get_current_user)):
    res = await db.medications.update_one({"id": med_id, "user_id": user["user_id"]}, {"$set": {"deleted_at": now_iso()}})
    if not res.matched_count:
        raise HTTPException(status_code=404, detail="Medication not found")
    return {"ok": True, "recoverable_days": RECOVERY_DAYS}


@router.get("/reminders")
async def list_reminders(user=Depends(get_current_user)):
    items = await db.reminders.find({"user_id": user["user_id"], "deleted_at": None}, NO_ID).sort("time", 1).to_list(200)
    return items


@router.get("/reminders/today")
async def reminders_today(day: Optional[str] = None, user=Depends(get_current_user)):
    day = _valid_date(day) if day else date.today().isoformat()
    weekday = date.fromisoformat(day).weekday()
    items = await db.reminders.find({"user_id": user["user_id"], "deleted_at": None, "active": True}, NO_ID).to_list(200)
    due = [r for r in items if (r.get("date") == day) or (not r.get("date") and weekday in r.get("days", []))]
    for r in due:
        r["done"] = day in r.get("done_dates", [])
    return sorted(due, key=lambda r: r["time"])


@router.post("/reminders", status_code=201)
async def create_reminder(body: ReminderIn, user=Depends(get_current_user)):
    doc = {"id": str(uuid.uuid4()), "user_id": user["user_id"], **body.model_dump(), "done_dates": [], "created_at": now_iso(), "deleted_at": None}
    await db.reminders.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.put("/reminders/{rem_id}")
async def update_reminder(rem_id: str, body: ReminderIn, user=Depends(get_current_user)):
    res = await db.reminders.update_one({"id": rem_id, "user_id": user["user_id"]}, {"$set": body.model_dump()})
    if not res.matched_count:
        raise HTTPException(status_code=404, detail="Reminder not found")
    updated = await db.reminders.find_one({"id": rem_id}, NO_ID)
    return updated


@router.post("/reminders/{rem_id}/done")
async def reminder_done(rem_id: str, day: Optional[str] = None, undo: bool = False, user=Depends(get_current_user)):
    day = _valid_date(day) if day else date.today().isoformat()
    op = {"$pull": {"done_dates": day}} if undo else {"$addToSet": {"done_dates": day}}
    res = await db.reminders.update_one({"id": rem_id, "user_id": user["user_id"]}, op)
    if not res.matched_count:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"ok": True}


@router.delete("/reminders/{rem_id}")
async def delete_reminder(rem_id: str, user=Depends(get_current_user)):
    res = await db.reminders.update_one({"id": rem_id, "user_id": user["user_id"]}, {"$set": {"deleted_at": now_iso()}})
    if not res.matched_count:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"ok": True, "recoverable_days": RECOVERY_DAYS}
