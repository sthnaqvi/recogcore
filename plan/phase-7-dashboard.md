# Phase 7 — Optional dashboard

**Est. 10–15 hrs** · See [../PLAN.md](../PLAN.md) for overall architecture and progress log.

## Goal
A simple web view over the `person_events` data (Phase 5) — who came and went, when, with
snapshots — closing out the Mac MVP. Explicitly optional/lower-priority relative to Phases 0–6.

## Task breakdown

1. Decide the frontend approach: a plain server-rendered view from the existing
   `backend/` Express app (simplest — no new build tooling) vs a small separate
   React/Vite app. Recommendation: server-rendered (e.g. Express + a templating engine, or a
   single static HTML page hitting the existing `GET /api/events` JSON API with fetch) — this is
   explicitly the lowest-effort option and the phase is already marked optional.
2. Add `backend/src/routes/dashboard.js` (or extend `events.js`) serving a static page under
   `backend/public/` that fetches `GET /api/events` and renders a table: timestamp, person_name,
   is_known, confidence, event_type.
3. Serve snapshot images referenced by `snapshot_path` — add a static file route
   (`express.static`) scoped to `data/snapshots/` so the dashboard can show a thumbnail per
   event without duplicating image storage.
4. Add basic filtering in the UI (by person, date range, known/unknown) backed by the existing
   `GET /api/events` query params from Phase 5 — no new backend logic if Phase 5's filters
   already cover this, otherwise extend them.
5. Add simple pagination to `GET /api/events` (`limit`/`offset`) and the dashboard table, since
   `person_events` grows unbounded over time.
6. No authentication is required for the MVP (local-network-only tool), but note this
   explicitly in `backend/README.md` as a known limitation if the backend is ever exposed beyond
   localhost.
7. Manual verification: run backend + a populated `person_events` table (from Phase 6 testing),
   load the dashboard in a browser, confirm the table renders, thumbnails load, and filters/
   pagination work.

## File/folder layout created by this phase

```
backend/
├── public/
│   ├── index.html
│   ├── dashboard.js
│   └── dashboard.css
└── src/
    └── routes/
        └── dashboard.js            # only if serving via a dedicated route/template, not just static files
```
