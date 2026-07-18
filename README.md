# RecogCore

A stationary home-entryway assistant: camera + mic + speaker, no motion. Recognizes trained
family members and greets them by name, greets unknown faces generically, holds a two-way
conversation, and logs every entry/exit. Built and tested on Mac first; a Raspberry Pi
deployment is added later behind the same hardware abstraction layer — see [PLAN.md](PLAN.md)
for the full phase-by-phase roadmap.

## Setup (Mac)

```bash
cd python-service
python3.10 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cd ..
cp config.example.yaml config.yaml
cp .env.example .env

cd python-service
python scripts/smoke_test.py
```

`config.yaml` and `.env` are your local, gitignored copies — never commit them. See
[data/README.md](data/README.md) for where trained faces, embeddings, and other local runtime
data live (also gitignored, kept separate from this repo's code).

## Tests

```bash
cd python-service
pytest
```
