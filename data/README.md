# `data/` — local, private, gitignored

Nothing in this directory is ever committed (see root `.gitignore`: `data/training/` and
`data/runtime/` are both fully ignored). This file is the only thing under `data/` that's
tracked by git — it exists purely to document the expected layout for a fresh clone.

The split is deliberate: **training data** (your family's faces) and **runtime data**
(everything the system generates while running) are kept in separate subtrees, even though
both are equally gitignored, so it's obvious at a glance which one you'd back up/migrate
by hand (`training/`) versus which one is disposable/regeneratable (`runtime/`).

```
data/
├── training/                  # YOUR personal training data — never shared, never committed
│   ├── faces/<person_name>/   # raw captured training photos (Phase 2)
│   │   └── *.jpg
│   └── embeddings/            # generated face embeddings (Phase 2)
│       └── known_faces.pkl
└── runtime/                   # other local generated data — safe to wipe and regenerate
    ├── snapshots/             # per-event JPEG crops referenced by person_events.snapshot_path (Phase 5)
    ├── db/                    # local MySQL data files / dumps, if run locally rather than via a managed DB
    └── logs/                  # application logs (Phase 6+)
```

The real runtime config (`config.yaml`, copied from the committed `config.example.yaml`) lives
at the **repo root**, not under `data/` — it's gitignored the same way, just kept alongside
`config.example.yaml` so the two are easy to diff.
