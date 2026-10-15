from typing import Literal, Optional

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from auth import get_current_user
from db import db, NO_ID, now_iso, audit

router = APIRouter(prefix="/me", tags=["account"])
CONSENT_VERSION = "2026-06"
USER_COLLECTIONS = ["day_logs", "medications", "reminders", "chat_sessions", "chat_messages", "reports", "audit_logs", "user_sessions"]


class ConsentIn(BaseModel):
    accepted: bool


class SettingsIn(BaseModel):
    cycle_context: Optional[Literal["regular", "irregular", "unknown", "pregnancy", "postpartum", "menopause", "not_applicable"]] = None
    language: Optional[Literal["en", "hi", "kn", "ta", "ml"]] = None
    lock_timeout_min: Optional[int] = Field(default=None, ge=1, le=120)
    reduced_motion: Optional[bool] = None


class PinIn(BaseModel):
    pin: str = Field(min_length=4, max_length=8, pattern=r"^\d+$")


@router.put("/consent")
async def set_consent(body: ConsentIn, user=Depends(get_current_user)):
    consent = {"accepted": body.accepted, "version": CONSENT_VERSION, "at": now_iso()} if body.accepted else None
    await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"consent": consent}})
    await audit(user["user_id"], "consent_updated", {"accepted": body.accepted, "version": CONSENT_VERSION})
    return {"consent": consent}


@router.put("/settings")
async def update_settings(body: SettingsIn, user=Depends(get_current_user)):
    updates = {f"settings.{k}": v for k, v in body.model_dump(exclude_none=True).items()}
    if updates:
        await db.users.update_one({"user_id": user["user_id"]}, {"$set": updates})
    doc = await db.users.find_one({"user_id": user["user_id"]}, NO_ID)
    return doc["settings"]


@router.post("/lock")
async def set_lock(body: PinIn, user=Depends(get_current_user)):
    pin_hash = bcrypt.hashpw(body.pin.encode(), bcrypt.gensalt()).decode()
    await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"lock_pin_hash": pin_hash, "settings.lock_enabled": True}})
    await audit(user["user_id"], "lock_enabled", {})
    return {"lock_enabled": True}


@router.post("/lock/verify")
async def verify_lock(body: PinIn, user=Depends(get_current_user)):
    full = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0, "lock_pin_hash": 1})
    stored = (full or {}).get("lock_pin_hash")
    if not stored or not bcrypt.checkpw(body.pin.encode(), stored.encode()):
        raise HTTPException(status_code=403, detail="Incorrect PIN")
    return {"ok": True}


@router.delete("/lock")
async def remove_lock(body: PinIn, user=Depends(get_current_user)):
    await verify_lock(body, user)
    await db.users.update_one({"user_id": user["user_id"]}, {"$unset": {"lock_pin_hash": ""}, "$set": {"settings.lock_enabled": False}})
    await audit(user["user_id"], "lock_disabled", {})
    return {"lock_enabled": False}


@router.get("/export")
async def export_data(user=Depends(get_current_user)):
    uid = user["user_id"]
    out = {"exported_at": now_iso(), "profile": {k: v for k, v in user.items() if k not in ("lock_pin_hash", "_session_id")}}
    for name in ["day_logs", "medications", "reminders", "chat_sessions", "chat_messages", "reports"]:
        out[name] = await db[name].find({"user_id": uid}, {"_id": 0, "user_id": 0, "storage_path": 0, "pdf_bytes": 0}).to_list(5000)
    await audit(uid, "data_exported", {})
    return out


@router.get("/audit")
async def my_audit(user=Depends(get_current_user)):
    items = await db.audit_logs.find({"user_id": user["user_id"]}, NO_ID).sort("at", -1).to_list(100)
    return items


@router.delete("")
async def delete_account(response: Response, user=Depends(get_current_user)):
    uid = user["user_id"]
    for name in USER_COLLECTIONS:
        await db[name].delete_many({"user_id": uid})
    await db.users.delete_one({"user_id": uid})
    response.delete_cookie("session_token", path="/", secure=True, samesite="none")
    return {"deleted": True}
