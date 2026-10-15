import logging
import os

from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware

from db import db, client
import auth, routes_logs, routes_account, routes_chat, routes_reports
import storage

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="ForHer API")
api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"app": "ForHer", "status": "ok"}


for r in (auth.router, routes_logs.router, routes_account.router, routes_chat.router, routes_reports.router):
    api_router.include_router(r)
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await db.users.create_index("user_id", unique=True)
    await db.users.create_index("email", unique=True)
    await db.user_sessions.create_index("session_token", unique=True)
    await db.day_logs.create_index([("user_id", 1), ("date", 1)])
    await db.chat_messages.create_index([("session_id", 1), ("created_at", 1)])
    await db.reports.create_index("share_token", sparse=True)
    try:
        storage.init_storage()
        logger.info("Object storage initialised")
    except Exception as exc:
        logger.error("Object storage init failed: %s", exc)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
