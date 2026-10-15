import json
import os
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone

from auth import get_current_user
from db import db, NO_ID, now_iso, audit
from safety import (SYSTEM_PROMPT, SOURCES, SOURCES_VERSION, sources_for, is_urgent, is_self_harm,
                    localized, language_instruction, post_check)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])

RESOURCES = [
    {"id": "fogsi", "name": "FOGSI — Find a gynaecologist (India)", "type": "directory", "url": "https://www.fogsi.org/", "region": "India",
     "note": "Professional body of obstetricians and gynaecologists in India."},
    {"id": "nhs-find", "name": "NHS — Find a GP (UK)", "type": "directory", "url": "https://www.nhs.uk/service-search/find-a-gp", "region": "UK", "note": "Register with a local GP for referrals."},
    {"id": "acog-find", "name": "ACOG — Find an Ob-Gyn (US)", "type": "directory", "url": "https://www.acog.org/womens-health/find-an-ob-gyn", "region": "US", "note": ""},
    {"id": "telemanas", "name": "Tele-MANAS mental health helpline (India) — 14416", "type": "helpline", "url": "https://telemanas.mohfw.gov.in/", "region": "India", "note": "Free, 24x7."},
    {"id": "emergency-in", "name": "Emergency services (India) — 112", "type": "helpline", "url": "", "region": "India", "note": "For heavy bleeding with fainting, severe pain, or pregnancy bleeding."},
]


class SessionIn(BaseModel):
    title: str = Field(default="New conversation", max_length=80)


class MessageIn(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


def _sse(obj: dict) -> str:
    return f"data: {json.dumps(obj)}\n\n"


@router.get("/sources")
async def sources():
    return {"version": SOURCES_VERSION, "sources": SOURCES}


@router.get("/resources")
async def resources():
    return {"disclaimer": "This directory is general referral information, not a personalised recommendation.", "resources": RESOURCES}


@router.get("/sessions")
async def list_sessions(user=Depends(get_current_user)):
    items = await db.chat_sessions.find({"user_id": user["user_id"]}, NO_ID).sort("created_at", -1).to_list(50)
    return items


@router.post("/sessions", status_code=201)
async def create_session(body: SessionIn, user=Depends(get_current_user)):
    doc = {"id": str(uuid.uuid4()), "user_id": user["user_id"], "title": body.title, "created_at": now_iso()}
    await db.chat_sessions.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.delete("/sessions/{sid}")
async def delete_session(sid: str, user=Depends(get_current_user)):
    await db.chat_sessions.delete_one({"id": sid, "user_id": user["user_id"]})
    await db.chat_messages.delete_many({"session_id": sid, "user_id": user["user_id"]})
    return {"ok": True}


@router.get("/sessions/{sid}/messages")
async def list_messages(sid: str, user=Depends(get_current_user)):
    items = await db.chat_messages.find({"session_id": sid, "user_id": user["user_id"]}, NO_ID).sort("created_at", 1).to_list(500)
    return items


@router.post("/sessions/{sid}/messages")
async def send_message(sid: str, body: MessageIn, user=Depends(get_current_user)):
    session = await db.chat_sessions.find_one({"id": sid, "user_id": user["user_id"]}, NO_ID)
    if not session:
        raise HTTPException(status_code=404, detail="Conversation not found")
    uid = user["user_id"]
    text = body.content.strip()
    urgent, self_harm = is_urgent(text), is_self_harm(text)
    picked_sources = sources_for(text)
    await db.chat_messages.insert_one({"id": str(uuid.uuid4()), "session_id": sid, "user_id": uid, "role": "user", "content": text,
                                       "created_at": now_iso(), "flags": {"urgent": urgent}})
    if session["title"] == "New conversation":
        await db.chat_sessions.update_one({"id": sid}, {"$set": {"title": text[:60]}})
    history = await db.chat_messages.find({"session_id": sid, "user_id": uid}, NO_ID).sort("created_at", 1).to_list(500)
    ctx = user.get("settings", {})
    lang = ctx.get("language", "en") if ctx.get("language") in ("en", "hi") else "en"
    system = SYSTEM_PROMPT + language_instruction(lang) + f"\nUser context (self-reported): cycle context = {ctx.get('cycle_context', 'unknown')}."
    initial = [{"role": "system", "content": system}] + [{"role": m["role"], "content": m["content"]} for m in history[-20:-1]]

    async def gen():
        full = ""
        yield _sse({"type": "meta", "urgent": urgent, "self_harm": self_harm, "sources": picked_sources, "language": lang})
        if self_harm:
            note = localized("self_harm", lang) + "\n\n"
            yield _sse({"type": "delta", "content": note}); full += note
        elif urgent:
            note = localized("urgent", lang) + "\n\n"
            yield _sse({"type": "delta", "content": note}); full += note
        error = None
        try:
            chat = LlmChat(api_key=os.environ.get("EMERGENT_LLM_KEY"), session_id=sid, system_message=system,
                           initial_messages=initial).with_model("anthropic", "claude-sonnet-5-5")
            async for ev in chat.stream_message(UserMessage(text=text)):
                if isinstance(ev, TextDelta):
                    full += ev.content
                    yield _sse({"type": "delta", "content": ev.content})
                elif isinstance(ev, StreamDone):
                    break
        except Exception as exc:  # provider failure → text fallback
            logger.error("LLM error: %s", exc)
            error = "ai_unavailable"
            fb = localized("fallback", lang)
            full += fb
            yield _sse({"type": "delta", "content": fb})
        checked, flags = post_check(full, lang)
        if flags:
            extra = checked[len(full):]
            yield _sse({"type": "delta", "content": extra})
        mid = str(uuid.uuid4())
        await db.chat_messages.insert_one({"id": mid, "session_id": sid, "user_id": uid, "role": "assistant", "content": checked,
                                           "created_at": now_iso(), "sources": picked_sources, "flags": {"post_check": flags, "error": error}})
        if flags or error:
            await audit(uid, "chat_safety_event", {"post_check_flags": len(flags), "error": error})
        yield _sse({"type": "done", "message_id": mid, "error": error, "sources": picked_sources, "language": lang})

    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
