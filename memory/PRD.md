# ForHer — PRD & Build Log

## Original problem statement
Accessible, privacy-first cycle-awareness web app (formerly "Luna"). Log period/flow/mood/symptoms/medications/notes/reminders; clearly-labelled cycle estimates; empathetic non-diagnostic AI chat with safety policy and curated sources; separate physician/resource directory; personal + clinician reports with PDF; Google auth; cloud sync, export, permanent deletion, consent, session/device management; in-app reminders; app lock; WCAG 2.2 AA accessibility; English first, Indian languages staged later.

## User choices (June 2026)
- AI: Claude Sonnet 5.5 via Emergent Universal Key (anthropic/claude-sonnet-5-5)
- Auth: Emergent-managed Google login only
- Voice: text only for this release
- Scope: Phases 1–3 + English chat
- Prototype HTML: user intended to upload but no asset was attached — designed fresh from brief

## Architecture
- Frontend: React 19 (JSX, CRA/craco), Tailwind + shadcn/ui, react-query, recharts, PWA manifest + service worker (prod only). Fonts: Cormorant Garamond + Manrope. Palette from /app/design_guidelines.json.
- Backend: FastAPI modules — auth.py (Emergent session exchange, cookie+Bearer), routes_logs.py (logs/trash/estimate/meds/reminders), routes_account.py (consent/settings/lock/export/delete/audit), routes_chat.py (SSE chat, safety, sources, resources), routes_reports.py (summary/PDF/share), cycles.py, reports.py (reportlab), safety.py, storage.py (Emergent Object Storage).
- DB (Mongo): users, user_sessions, day_logs (version + deleted_at), medications, reminders (done_dates), chat_sessions, chat_messages, reports (storage_path or pdf_bytes fallback, share_token/expiry), audit_logs.

## User personas
- Regular/irregular cycle trackers wanting gentle logging + patterns
- Users with pregnancy/postpartum/menopause context (estimates paused)
- Users preparing a clinician visit (doctor summary + PDF + share link)

## Implemented (2026-06)
- Landing with hero (pink gradient overlay), Google sign-in, boundaries copy
- Consent dialog (versioned), settings: cycle context, language (en live; hi/kn/ta/ml disabled "coming soon"), reduced motion
- Calendar grid (aria-labelled days, estimate window "est." labels, legend), day log sheet (period/flow/mood/symptoms/meds/notes), local drafts, offline flush, 409 conflict dialog (keep mine / use server)
- Soft delete with 30-day recovery (logs/meds/reminders) + restore in Settings
- Cycle estimate with confidence tiers; disabled with reason for pregnancy/postpartum/menopause/not_applicable
- Medications CRUD, reminders CRUD (repeat days / one-off), today's reminders + done/undo (in-app only)
- Reports: summary (personal/doctor), recharts symptoms, limitations, PDF via reportlab → Object Storage, download, 7-day public share link + /share/:token page
- AI chat: SSE streaming, safety pre-check (urgent/self-harm notes), post-check for diagnostic phrasing, curated versioned sources, text fallback on provider failure, retry UI
- App lock (bcrypt PIN, inactivity timeout, manual lock), sessions list/revoke/logout-all, JSON export, permanent account deletion, audit log
- Testing: iteration_1 — backend 25/25 pass; frontend all flows pass after Chat render fix
- Period Check-In: dashboard prompt inside estimated window ("Yes, log today" presets period+medium flow in log sheet; "Not yet" dismisses for the day via localStorage; link to Settings for context)
- Symptom Trends: summary.symptom_trends (estimated phases menstrual/follicular/ovulatory/luteal, or period-vs-other when estimates paused) with stacked bar chart + accessible table in Reports and a table in the PDF
- Testing: iteration_2 — all passed after fixing check-in dismissal persistence
- Cycle History: GET /cycles/history (lengths, change vs previous, 7+ day changes highlighted) + Reports timeline chart/list + PDF table
- Mood Trends: summary.mood_trends per estimated phase, Reports section + PDF table
- Hindi: i18n layer (src/lib/i18n.js, useT) for nav/dashboard/calendar/log sheet/chat/check-in/estimate/settings; dayjs hi locale; html lang; chat replies in Hindi via system prompt with English fallback; Hindi urgent/self-harm/fallback notes. Backend prose (estimate reasons, limitations, history note) still English.
- Testing: iteration_3 — all passed

## Backlog
- P0: none known
- P1: Hindi/Kannada/Tamil/Malayalam UI + chat (staged); voice input/output with text fallback; TypeScript migration if required
- P2: Richer conflict diff UI; report trends over multiple ranges; OS notifications (consented channel); accessibility audit pass with screen-reader users; backups/observability
