import os
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

client = AsyncIOMotorClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]

NO_ID = {"_id": 0}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def audit(user_id: str, action: str, meta: dict | None = None):
    await db.audit_logs.insert_one(
        {"user_id": user_id, "action": action, "meta": meta or {}, "at": now_iso()}
    )
