import asyncio
import uuid
from datetime import datetime, timezone, timedelta

import requests
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from db import db, NO_ID, now_iso, audit

router = APIRouter(prefix="/auth", tags=["auth"])
SESSION_DAYS = 7
EMERGENT_SESSION_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"


class SessionExchange(BaseModel):
    session_id: str


def _parse_dt(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value


def _token_from_request(request: Request) -> str | None:
    token = request.cookies.get("session_token")
    if token:
        return token
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:]
    return None


async def get_session(request: Request) -> dict:
    token = _token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": token}, NO_ID)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    if _parse_dt(session["expires_at"]) < datetime.now(timezone.utc):
        await db.user_sessions.delete_one({"session_token": token})
        raise HTTPException(status_code=401, detail="Session expired")
    await db.user_sessions.update_one({"session_token": token}, {"$set": {"last_seen": now_iso()}})
    return session


async def get_current_user(request: Request) -> dict:
    session = await get_session(request)
    user = await db.users.find_one({"user_id": session["user_id"]}, NO_ID)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    user["_session_id"] = session.get("id")
    return user


def set_session_cookie(response: Response, token: str):
    response.set_cookie(
        "session_token", token, httponly=True, secure=True, samesite="none",
        path="/", max_age=SESSION_DAYS * 24 * 3600,
    )


@router.post("/session")
async def exchange_session(body: SessionExchange, request: Request, response: Response):
    def fetch():
        return requests.get(EMERGENT_SESSION_URL, headers={"X-Session-ID": body.session_id}, timeout=20)

    resp = await asyncio.to_thread(fetch)
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Could not verify Google sign-in")
    data = resp.json()
    email = data["email"]
    user = await db.users.find_one({"email": email}, NO_ID)
    if user:
        await db.users.update_one(
            {"email": email}, {"$set": {"name": data.get("name"), "picture": data.get("picture")}}
        )
        user_id = user["user_id"]
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        await db.users.insert_one({
            "user_id": user_id, "email": email, "name": data.get("name"),
            "picture": data.get("picture"), "created_at": now_iso(),
            "consent": None,
            "settings": {
                "cycle_context": "unknown", "language": "en",
                "lock_enabled": False, "lock_timeout_min": 5, "reduced_motion": False,
            },
        })
    token = data["session_token"]
    await db.user_sessions.insert_one({
        "id": str(uuid.uuid4()), "user_id": user_id, "session_token": token,
        "created_at": now_iso(), "last_seen": now_iso(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)).isoformat(),
        "user_agent": request.headers.get("user-agent", "")[:160],
    })
    set_session_cookie(response, token)
    await audit(user_id, "login", {})
    created = await db.users.find_one({"user_id": user_id}, NO_ID)
    return {k: v for k, v in created.items() if k not in ("_id", "lock_pin_hash")}


@router.get("/me")
async def me(request: Request):
    user = await get_current_user(request)
    return {k: v for k, v in user.items() if k != "lock_pin_hash"}


@router.post("/logout")
async def logout(request: Request, response: Response):
    token = _token_from_request(request)
    if token:
        await db.user_sessions.delete_one({"session_token": token})
    response.delete_cookie("session_token", path="/", secure=True, samesite="none")
    return {"ok": True}


@router.get("/sessions")
async def list_sessions(request: Request):
    user = await get_current_user(request)
    sessions = await db.user_sessions.find({"user_id": user["user_id"]}, {"_id": 0, "session_token": 0}).to_list(100)
    for s in sessions:
        s["current"] = s["id"] == user["_session_id"]
    return sessions


@router.delete("/sessions/{session_id}")
async def revoke_session(session_id: str, request: Request):
    user = await get_current_user(request)
    await db.user_sessions.delete_one({"id": session_id, "user_id": user["user_id"]})
    await audit(user["user_id"], "session_revoked", {})
    return {"ok": True}


@router.post("/logout-all")
async def logout_all(request: Request, response: Response):
    user = await get_current_user(request)
    await db.user_sessions.delete_many({"user_id": user["user_id"]})
    response.delete_cookie("session_token", path="/", secure=True, samesite="none")
    await audit(user["user_id"], "logout_all", {})
    return {"ok": True}
