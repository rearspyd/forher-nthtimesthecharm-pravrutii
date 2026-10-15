import asyncio
import logging
import secrets
import uuid
from datetime import date, datetime, timezone, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel

from auth import get_current_user
from db import db, NO_ID, now_iso, audit
from reports import build_summary, render_pdf
import storage

logger = logging.getLogger(__name__)
router = APIRouter(tags=["reports"])
SHARE_DAYS = 7


class PdfIn(BaseModel):
    from_: str
    to: str
    mode: Literal["personal", "doctor"] = "personal"

    model_config = {"populate_by_name": True}


def _range(from_: str, to: str):
    try:
        a, b = date.fromisoformat(from_), date.fromisoformat(to)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date range")
    if a > b or (b - a).days > 400:
        raise HTTPException(status_code=400, detail="Range must be ascending and at most 400 days")
    return a.isoformat(), b.isoformat()


async def _summary(user: dict, from_: str, to: str, mode: str) -> dict:
    uid = user["user_id"]
    logs = await db.day_logs.find({"user_id": uid, "date": {"$gte": from_, "$lte": to}, "deleted_at": None}, NO_ID).sort("date", 1).to_list(500)
    meds = await db.medications.find({"user_id": uid}, NO_ID).to_list(200)
    return build_summary(logs, meds, user, from_, to, mode)


@router.get("/reports/summary")
async def report_summary(from_: str = Query(alias="from"), to: str = Query(), mode: Literal["personal", "doctor"] = "personal", user=Depends(get_current_user)):
    a, b = _range(from_, to)
    return await _summary(user, a, b, mode)


@router.get("/reports")
async def list_reports(user=Depends(get_current_user)):
    return await db.reports.find({"user_id": user["user_id"]}, {"_id": 0, "storage_path": 0, "pdf_bytes": 0, "share_token": 0}).sort("created_at", -1).to_list(50)


@router.post("/reports/pdf", status_code=201)
async def create_pdf(body: dict, user=Depends(get_current_user)):
    a, b = _range(body.get("from", ""), body.get("to", ""))
    mode = body.get("mode", "personal")
    if mode not in ("personal", "doctor"):
        raise HTTPException(status_code=400, detail="Invalid mode")
    summary = await _summary(user, a, b, mode)
    pdf = await asyncio.to_thread(render_pdf, summary)
    rid = str(uuid.uuid4())
    path = f"{storage.APP_NAME}/reports/{user['user_id']}/{rid}.pdf"
    doc = {"id": rid, "user_id": user["user_id"], "mode": mode, "from": a, "to": b, "created_at": now_iso(), "size": len(pdf), "storage": "object_storage"}
    try:
        result = await asyncio.to_thread(storage.put_object, path, pdf, "application/pdf")
        doc["storage_path"] = result["path"]
    except Exception as exc:
        logger.error("Object storage failed, keeping PDF in database: %s", exc)
        doc["storage"] = "database"
        doc["pdf_bytes"] = pdf
    await db.reports.insert_one(doc)
    await audit(user["user_id"], "report_generated", {"mode": mode})
    return {k: v for k, v in doc.items() if k not in ("_id", "storage_path", "pdf_bytes")}


async def _load_pdf(report: dict) -> bytes:
    if report.get("storage") == "database":
        return bytes(report["pdf_bytes"])
    return await asyncio.to_thread(storage.get_object, report["storage_path"])


@router.get("/reports/{rid}/download")
async def download_pdf(rid: str, user=Depends(get_current_user)):
    report = await db.reports.find_one({"id": rid, "user_id": user["user_id"]}, NO_ID)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    pdf = await _load_pdf(report)
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="forher-report-{report["from"]}-to-{report["to"]}.pdf"'})


@router.post("/reports/{rid}/share")
async def share_report(rid: str, user=Depends(get_current_user)):
    report = await db.reports.find_one({"id": rid, "user_id": user["user_id"]}, NO_ID)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    token = secrets.token_urlsafe(24)
    expires = (datetime.now(timezone.utc) + timedelta(days=SHARE_DAYS)).isoformat()
    await db.reports.update_one({"id": rid}, {"$set": {"share_token": token, "share_expires_at": expires}})
    await audit(user["user_id"], "report_shared", {"report_id": rid})
    return {"token": token, "expires_at": expires}


@router.delete("/reports/{rid}/share")
async def unshare_report(rid: str, user=Depends(get_current_user)):
    await db.reports.update_one({"id": rid, "user_id": user["user_id"]}, {"$unset": {"share_token": "", "share_expires_at": ""}})
    return {"ok": True}


async def _shared(token: str) -> dict:
    report = await db.reports.find_one({"share_token": token}, NO_ID)
    if not report or datetime.fromisoformat(report["share_expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=404, detail="This link has expired or does not exist")
    return report


@router.get("/share/{token}")
async def shared_summary(token: str):
    report = await _shared(token)
    user = await db.users.find_one({"user_id": report["user_id"]}, NO_ID)
    summary = await _summary(user, report["from"], report["to"], "doctor")
    summary["expires_at"] = report["share_expires_at"]
    return summary


@router.get("/share/{token}/pdf")
async def shared_pdf(token: str):
    report = await _shared(token)
    pdf = await _load_pdf(report)
    return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition": 'inline; filename="forher-summary.pdf"'})
