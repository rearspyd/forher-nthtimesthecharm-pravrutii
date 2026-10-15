"""Tests for 3 new features: Cycle History, Mood Trends, Hindi i18n.

Target user: test-user-qa (session token: test_session_qa).
"""
import os
import json
import io
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://forher-staging.preview.emergentagent.com").rstrip("/")
API = BASE_URL + "/api"
TOKEN = "test_session_qa"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}


# ------------------- Cycle History -------------------
class TestCycleHistory:
    def test_cycles_history(self):
        r = requests.get(f"{API}/cycles/history", headers=HEADERS)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "cycles" in data
        cycles = data["cycles"]
        for c in cycles:
            for k in ["start", "period_end", "period_length", "cycle_length", "complete", "change_from_previous"]:
                assert k in c, f"missing key {k} in cycle {c}"
        # expected summary
        assert data.get("completed_cycles") == 2, data
        assert data.get("shortest") == 28, data
        assert data.get("longest") == 113, data
        assert data.get("variation") == 85, data
        notable = data.get("notable_changes") or []
        assert any("2026-05-30" in str(n) for n in notable), notable


# ------------------- Reports Summary + PDF -------------------
class TestReportsNew:
    def test_summary_includes_mood_and_history(self):
        r = requests.get(f"{API}/reports/summary", headers=HEADERS,
                         params={"from": "2026-04-01", "to": "2026-10-31"})
        assert r.status_code == 200, r.text
        data = r.json()
        assert "mood_trends" in data, list(data.keys())
        assert "cycle_history" in data, list(data.keys())
        mt = data["mood_trends"]
        # same shape as symptom_trends
        assert "method" in mt or "phases" in mt or "rows" in mt or "items" in mt, mt
        # Irritable row should exist with counts under follicular/ovulatory/luteal
        payload = json.dumps(mt)
        assert "Irritable" in payload, mt

    def test_pdf_contains_mood_and_history(self):
        r = requests.post(f"{API}/reports/pdf", headers=HEADERS,
                          json={"from": "2026-04-01", "to": "2026-10-31", "mode": "doctor"})
        assert r.status_code == 201, r.text
        rid = r.json()["id"]
        d = requests.get(f"{API}/reports/{rid}/download", headers=HEADERS)
        assert d.status_code == 200
        assert d.headers["content-type"].startswith("application/pdf")
        # Extract text from PDF
        try:
            from pypdf import PdfReader
        except ImportError:
            from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(d.content))
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
        assert "Moods by estimated cycle phase" in text, text[:2000]
        assert "Cycle history" in text, text[:2000]


# ------------------- Hindi Chat -------------------
class TestHindiChat:
    def test_language_invalid_rejected(self):
        r = requests.put(f"{API}/me/settings", headers=HEADERS, json={"language": "xx"})
        assert r.status_code in (400, 422), r.text

    def test_language_tamil_accepted(self):
        r = requests.put(f"{API}/me/settings", headers=HEADERS, json={"language": "ta"})
        assert r.status_code == 200, r.text
        # revert
        requests.put(f"{API}/me/settings", headers=HEADERS, json={"language": "en"})

    def _stream(self, sid, content):
        r = requests.post(f"{API}/chat/sessions/{sid}/messages",
                          headers=HEADERS, json={"content": content},
                          stream=True, timeout=90)
        assert r.status_code == 200, r.text
        meta = None
        deltas = []
        done = None
        for line in r.iter_lines():
            if not line or not line.startswith(b"data: "):
                continue
            payload = json.loads(line[6:])
            t = payload.get("type")
            if t == "meta":
                meta = payload
            elif t == "delta":
                deltas.append(payload.get("content") or payload.get("text") or payload.get("delta") or "")
            elif t == "done":
                done = payload
                break
        return meta, "".join(deltas), done

    def test_hindi_chat_flow(self):
        # Set language to hi
        s = requests.put(f"{API}/me/settings", headers=HEADERS, json={"language": "hi"})
        assert s.status_code == 200, s.text
        try:
            sid = requests.post(f"{API}/chat/sessions", headers=HEADERS, json={"title": "TEST_hi"}).json()["id"]
            meta, text, done = self._stream(sid, "क्या यह PCOS हो सकता है?")
            assert meta is not None and meta.get("language") == "hi", meta
            # Devanagari range
            assert any("\u0900" <= ch <= "\u097F" for ch in text), text[:500]
            assert "diagnose" not in text.lower() or "doctor" in text.lower() or "clinician" in text.lower() or "डॉक्टर" in text or "चिकित्सक" in text
            # Mentions a doctor/clinician in some form
            assert any(k in text.lower() for k in ["doctor", "clinician"]) or ("डॉक्टर" in text) or ("चिकित्सक" in text), text[:1000]
            assert done is not None and done.get("error") in (None, "null"), done

            # Urgent message (English triggers urgency regardless of language)
            sid2 = requests.post(f"{API}/chat/sessions", headers=HEADERS, json={"title": "TEST_hi_urgent"}).json()["id"]
            meta2, text2, done2 = self._stream(sid2, "soaking a pad every hour and feel faint")
            assert meta2 is not None and meta2.get("urgent") is True, meta2
            # Hindi urgent note at the start (contains Devanagari near the beginning)
            prefix = text2[:400]
            assert any("\u0900" <= ch <= "\u097F" for ch in prefix), prefix

            requests.delete(f"{API}/chat/sessions/{sid}", headers=HEADERS)
            requests.delete(f"{API}/chat/sessions/{sid2}", headers=HEADERS)
        finally:
            # restore language to en
            requests.put(f"{API}/me/settings", headers=HEADERS, json={"language": "en"})
