# Phase 5 — Metadata logging backend

**Est. 12–15 hrs** · See [../PLAN.md](../PLAN.md) for overall architecture and progress log.

## Goal
Every recognition event (Phase 2) gets logged with metadata — who, confidence, when, what kind
of event, and a snapshot — via a Node.js + MySQL backend that the Python service calls over a
local REST API.

## Task breakdown

1. Scaffold `backend/` as its own Node package: `npm init`, add `express` (or `fastify`),
   `mysql2`, `dotenv`, `nodemon` (dev). This is a separate installable unit from
   `python-service/`, per the open-source design constraint in `PLAN.md` — someone could in
   theory run just the backend against a different frontend.
2. The default schema already exists as a committed migration —
   [backend/migrations/001_create_person_events.sql](../backend/migrations/001_create_person_events.sql):
   ```sql
   CREATE TABLE person_events (
     id INT AUTO_INCREMENT PRIMARY KEY,
     person_name VARCHAR(50),        -- 'unknown' if stranger
     is_known BOOLEAN,
     confidence FLOAT,
     event_type ENUM('entry','exit','detected'),
     snapshot_path VARCHAR(255),
     timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
   );
   ```
   Migrations are schema, not private data, so — unlike `data/` — they're always committed
   rather than gitignored. This phase's job is wiring up a migration *runner*, not writing the
   SQL (already done).
3. Add a `backend/scripts/init_db.js` (or use a lightweight migration runner) that creates the
   local database/user and applies migrations — this is the "one command to get a working DB"
   step for a new contributor.
4. DB connection config lives in `backend/.env` (gitignored) populated from
   `backend/.env.example` (`DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`) — never a hardcoded
   connection string in code.
5. Write `backend/src/db.js`: a small `mysql2/promise` pool wrapper, single place all queries
   go through.
6. Write `backend/src/routes/events.js`: `POST /api/events` (create a `person_events` row from
   JSON body), `GET /api/events` (list/query with basic filters — by person, date range,
   event_type — used later by Phase 7's dashboard).
7. Add request validation on `POST /api/events` (required fields, `event_type` enum check,
   confidence range) — this is a boundary the Python service calls across a process/network
   edge, so validate here even though the caller is "trusted."
8. Snapshot handling: when Python logs a `detected`/`entry` event, it saves a JPEG crop to
   `data/runtime/snapshots/<timestamp>_<name>.jpg` (gitignored, alongside the `data/training/`
   tree from Phase 2 — snapshots are runtime output, not training input, hence the separate
   subtree) and sends the **path** (not the image bytes) in the API call;
   `snapshot_path` stores that path. Keep image transfer out of the REST payload for now — same
   filesystem is assumed since both services run on the same machine.
9. Write `recog_core/logging_client.py` on the Python side: a thin REST client
   (`requests`/`httpx`) with `log_event(person_name, is_known, confidence, event_type,
   snapshot_path)`, called from the Phase 2 recognition loop whenever a new recognition (or
   cooldown-gated re-recognition) occurs.
10. Decide and implement simple `entry` vs `exit` vs `detected` semantics: e.g. `detected` fires
    every distinct recognition, `entry` fires on transition from "not in view" → "in view" for a
    given person (track last-seen-at per person in the Python service, similar to the Phase 3
    greeting cooldown state), `exit` fires after N seconds of no detection for a previously-seen
    person.
11. Tests: `backend/tests/events.test.js` (route validation + DB insert/query against a test DB
    or mocked pool) and a Python-side test for `logging_client.py` (mocked HTTP call, confirms
    payload shape matches the API contract).
12. Manual verification: run backend + Python service together, walk through camera view,
    confirm rows appear in `person_events` with correct `event_type` transitions and a valid
    `snapshot_path` that actually points at a saved file.

## File/folder layout created by this phase

```
robot-assistant/
├── data/
│   └── runtime/
│       └── snapshots/              # gitignored — <timestamp>_<name>.jpg
└── backend/
    ├── package.json
    ├── .env.example
    ├── migrations/
    │   └── 001_create_person_events.sql   # already committed (ahead of this phase)
    ├── scripts/
    │   └── init_db.js
    ├── src/
    │   ├── db.js
    │   ├── app.js
    │   └── routes/
    │       └── events.js
    └── tests/
        └── events.test.js

python-service/
└── recog_core/
    └── logging_client.py
```
