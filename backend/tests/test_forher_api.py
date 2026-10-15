"""ForHer backend regression tests.

Covers: auth, consent, settings, logs (incl. conflict + soft-delete + restore),
cycle estimate, medications, reminders, reports (PDF + share), app lock, chat
sessions, resources/sources, export, and account deletion.
"""
import os
import time
import uuid
import json
import subprocess
import pytest
import requests
from datetime import date, timedelta

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://forher-staging.preview.emergentagent.com").rstrip("/")
API = BASE_URL + "/api"


def _mongo(script: str) -> str:
    out = subprocess.run(["mongosh", "--quiet", "--eval", script], capture_output=True, text=True, timeout=20)
    return out.stdout.strip()


def _make_user(consent_null: bool = True) -> tuple[str, str]:
    """Create a fresh test user + session in Mongo. Returns (user_id, session_token)."""
    ts = int(time.time() * 1000)
    uid = f"TEST_user_{ts}_{uuid.uuid4().hex[:6]}"
    tok = f"TEST_sess_{ts}_{uuid.uuid4().hex[:6]}"
    consent = "null" if consent_null else '{accepted:true,version:"2026-06",at:new Date().toISOString()}'
    script = f"""
use('test_database');
db.users.insertOne({{user_id:'{uid}', email:'{uid}@example.com', name:'QA', picture:'',
  created_at:new Date().toISOString(), consent:{consent},
  settings:{{cycle_context:'unknown', language:'en', lock_enabled:false, lock_timeout_min:5, reduced_motion:false}}}});
db.user_sessions.insertOne({{id:'sess-{ts}', user_id:'{uid}', session_token:'{tok}',
  expires_at:new Date(Date.now()+7*86400000).toISOString(), created_at:new Date().toISOString(),
  last_seen:new Date().toISOString(), user_agent:'pytest'}});
"""
    _mongo(script)
    return uid, tok


def _cleanup(uid: str):
    _mongo(f"""use('test_database');
db.users.deleteMany({{user_id:'{uid}'}});
db.user_sessions.deleteMany({{user_id:'{uid}'}});
db.day_logs.deleteMany({{user_id:'{uid}'}});
db.medications.deleteMany({{user_id:'{uid}'}});
db.reminders.deleteMany({{user_id:'{uid}'}});
db.chat_sessions.deleteMany({{user_id:'{uid}'}});
db.chat_messages.deleteMany({{user_id:'{uid}'}});
db.reports.deleteMany({{user_id:'{uid}'}});
db.audit_logs.deleteMany({{user_id:'{uid}'}});
""")


@pytest.fixture(scope="module")
def user():
    uid, tok = _make_user()
    yield uid, tok
    _cleanup(uid)


@pytest.fixture
def client(user):
    uid, tok = user
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    s.user_id = uid
    s.token = tok
    return s


# ------------------------- AUTH -------------------------
class TestAuth:
    def test_me_unauth_returns_401(self):
        r = requests.get(f"{API}/auth/me")
        assert r.status_code == 401

    def test_me_bearer(self, client):
        r = client.get(f"{API}/auth/me")
        assert r.status_code == 200
        data = r.json()
        assert data["user_id"] == client.user_id

    def test_me_cookie(self, user):
        uid, tok = user
        r = requests.get(f"{API}/auth/me", cookies={"session_token": tok})
        assert r.status_code == 200
        assert r.json()["user_id"] == uid

    def test_sessions_list(self, client):
        r = client.get(f"{API}/auth/sessions")
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list) and len(items) >= 1
        assert any(s.get("current") for s in items)


# ------------------------- CONSENT & SETTINGS -------------------------
class TestConsentAndSettings:
    def test_consent_initially_null(self, client):
        me = client.get(f"{API}/auth/me").json()
        assert me.get("consent") in (None, {}, "null")

    def test_set_consent(self, client):
        r = client.put(f"{API}/me/consent", json={"accepted": True})
        assert r.status_code == 200
        assert r.json()["consent"]["accepted"] is True
        me = client.get(f"{API}/auth/me").json()
        assert me["consent"]["accepted"] is True

    def test_update_settings_cycle_context(self, client):
        r = client.put(f"{API}/me/settings", json={"cycle_context": "regular"})
        assert r.status_code == 200
        assert r.json()["cycle_context"] == "regular"


# ------------------------- DAY LOGS -------------------------
class TestDayLogs:
    def test_create_log(self, client):
        d = "2026-10-10"
        r = client.put(f"{API}/logs/{d}", json={"period": True, "flow": "medium", "moods": ["happy"], "symptoms": ["cramps"], "notes": "test"})
        assert r.status_code == 200
        body = r.json()
        assert body["version"] == 1
        assert body["period"] is True and body["flow"] == "medium"
        # verify GET
        g = client.get(f"{API}/logs/{d}")
        assert g.status_code == 200
        assert g.json()["flow"] == "medium"

    def test_update_increments_version(self, client):
        d = "2026-10-10"
        r = client.put(f"{API}/logs/{d}", json={"period": True, "flow": "heavy", "base_version": 1})
        assert r.status_code == 200
        assert r.json()["version"] == 2

    def test_conflict_409(self, client):
        d = "2026-10-10"
        r = client.put(f"{API}/logs/{d}", json={"period": True, "flow": "light", "base_version": 1})
        assert r.status_code == 409
        detail = r.json()["detail"]
        assert "server" in detail

    def test_force_overwrites(self, client):
        d = "2026-10-10"
        r = client.put(f"{API}/logs/{d}", json={"period": True, "flow": "light", "base_version": 1, "force": True})
        assert r.status_code == 200
        assert r.json()["flow"] == "light"

    def test_list_logs_range(self, client):
        r = client.get(f"{API}/logs", params={"from": "2026-10-01", "to": "2026-10-31"})
        assert r.status_code == 200
        assert any(l["date"] == "2026-10-10" for l in r.json())

    def test_soft_delete_and_restore(self, client):
        d = "2026-10-11"
        client.put(f"{API}/logs/{d}", json={"period": False, "notes": "to delete"})
        r = client.delete(f"{API}/logs/{d}")
        assert r.status_code == 200
        trash = client.get(f"{API}/trash").json()
        trashed = [l for l in trash["logs"] if l["date"] == d]
        assert trashed, "deleted log should appear in trash"
        lid = trashed[0]["id"]
        rr = client.post(f"{API}/trash/logs/{lid}/restore")
        assert rr.status_code == 200
        g = client.get(f"{API}/logs/{d}").json()
        assert g.get("notes") == "to delete"


# ------------------------- CYCLE ESTIMATE -------------------------
class TestCycleEstimate:
    def test_estimate_enabled_with_periods(self, client):
        # ensure 2 period clusters
        for d in ["2026-08-01", "2026-08-02", "2026-09-01", "2026-09-02"]:
            client.put(f"{API}/logs/{d}", json={"period": True, "flow": "medium"})
        r = client.get(f"{API}/cycles/estimate")
        assert r.status_code == 200
        est = r.json()
        assert est["enabled"] is True
        assert est.get("next_period_estimate")

    def test_estimate_disabled_pregnancy(self, client):
        client.put(f"{API}/me/settings", json={"cycle_context": "pregnancy"})
        r = client.get(f"{API}/cycles/estimate")
        est = r.json()
        assert est["enabled"] is False
        assert est.get("reason")
        # restore
        client.put(f"{API}/me/settings", json={"cycle_context": "regular"})


# ------------------------- MEDICATIONS -------------------------
class TestMedications:
    def test_crud(self, client):
        r = client.post(f"{API}/medications", json={"name": "TEST_Vitamin", "dose": "500mg", "schedule": "daily", "active": True})
        assert r.status_code == 201
        mid = r.json()["id"]
        lst = client.get(f"{API}/medications").json()
        assert any(m["id"] == mid for m in lst)
        u = client.put(f"{API}/medications/{mid}", json={"name": "TEST_Vitamin", "dose": "500mg", "schedule": "daily", "active": False})
        assert u.status_code == 200 and u.json()["active"] is False
        d = client.delete(f"{API}/medications/{mid}")
        assert d.status_code == 200


# ------------------------- REMINDERS -------------------------
class TestReminders:
    def test_create_and_done(self, client):
        r = client.post(f"{API}/reminders", json={"label": "TEST_rem", "kind": "custom", "time": "09:00", "days": [0, 1, 2, 3, 4, 5, 6]})
        assert r.status_code == 201
        rid = r.json()["id"]
        today = client.get(f"{API}/reminders/today").json()
        assert any(x["id"] == rid for x in today)
        d = client.post(f"{API}/reminders/{rid}/done")
        assert d.status_code == 200
        today2 = client.get(f"{API}/reminders/today").json()
        assert next(x for x in today2 if x["id"] == rid)["done"] is True
        u = client.post(f"{API}/reminders/{rid}/done", params={"undo": "true"})
        assert u.status_code == 200
        client.delete(f"{API}/reminders/{rid}")


# ------------------------- REPORTS -------------------------
class TestReports:
    def test_summary(self, client):
        r = client.get(f"{API}/reports/summary", params={"from": "2026-08-01", "to": "2026-10-31", "mode": "personal"})
        assert r.status_code == 200
        assert "stats" in r.json() or "days_logged" in json.dumps(r.json())

    def test_pdf_and_share(self, client):
        r = client.post(f"{API}/reports/pdf", json={"from": "2026-08-01", "to": "2026-10-31", "mode": "doctor"})
        assert r.status_code == 201, r.text
        rid = r.json()["id"]
        d = client.get(f"{API}/reports/{rid}/download")
        assert d.status_code == 200
        assert d.headers["content-type"].startswith("application/pdf")
        s = client.post(f"{API}/reports/{rid}/share")
        assert s.status_code == 200
        token = s.json()["token"]
        # Public access without auth
        pub = requests.get(f"{API}/share/{token}")
        assert pub.status_code == 200
        # Invalid token
        bad = requests.get(f"{API}/share/invalidtoken123")
        assert bad.status_code == 404


# ------------------------- APP LOCK -------------------------
class TestAppLock:
    def test_set_verify_wrong_remove(self, client):
        r = client.post(f"{API}/me/lock", json={"pin": "1234"})
        assert r.status_code == 200
        bad = client.post(f"{API}/me/lock/verify", json={"pin": "9999"})
        assert bad.status_code == 403
        ok = client.post(f"{API}/me/lock/verify", json={"pin": "1234"})
        assert ok.status_code == 200
        rm = client.request("DELETE", f"{API}/me/lock", json={"pin": "1234"})
        assert rm.status_code == 200


# ------------------------- CHAT -------------------------
class TestChat:
    def test_sources_and_resources_public_requires_auth(self, client):
        r = client.get(f"{API}/chat/sources")
        assert r.status_code == 200
        assert "sources" in r.json()
        r2 = client.get(f"{API}/chat/resources")
        assert r2.status_code == 200
        assert "resources" in r2.json()

    def test_session_crud(self, client):
        r = client.post(f"{API}/chat/sessions", json={"title": "TEST_chat"})
        assert r.status_code == 201
        sid = r.json()["id"]
        lst = client.get(f"{API}/chat/sessions").json()
        assert any(s["id"] == sid for s in lst)
        d = client.delete(f"{API}/chat/sessions/{sid}")
        assert d.status_code == 200

    def test_streaming_message_with_urgent(self, client):
        sid = client.post(f"{API}/chat/sessions", json={"title": "TEST_urgent"}).json()["id"]
        r = requests.post(f"{API}/chat/sessions/{sid}/messages",
                          headers={"Authorization": f"Bearer {client.token}", "Content-Type": "application/json"},
                          json={"content": "I am soaking a pad every hour and feel faint"},
                          stream=True, timeout=60)
        assert r.status_code == 200
        got_urgent = False
        for line in r.iter_lines():
            if not line:
                continue
            if line.startswith(b"data: "):
                payload = json.loads(line[6:])
                if payload.get("type") == "meta" and payload.get("urgent"):
                    got_urgent = True
                if payload.get("type") == "done":
                    break
        assert got_urgent, "urgent flag should be set"
        client.delete(f"{API}/chat/sessions/{sid}")


# ------------------------- EXPORT & DELETE -------------------------
class TestExportAndDelete:
    def test_export(self, client):
        r = client.get(f"{API}/me/export")
        assert r.status_code == 200
        data = r.json()
        assert "profile" in data and "day_logs" in data

    def test_delete_account_last(self):
        uid, tok = _make_user(consent_null=False)
        s = requests.Session()
        s.headers.update({"Authorization": f"Bearer {tok}"})
        d = s.delete(f"{API}/me")
        assert d.status_code == 200
        me = s.get(f"{API}/auth/me")
        assert me.status_code == 401
