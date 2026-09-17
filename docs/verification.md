# Local verification — October 7, 2026

- Python 3.11: `cd backend && ../.venv/bin/python -m pytest -q` — 32 passed. One upstream Starlette/AnyIO deprecation warning was reported.
- Node 26: `cd frontend && npm ci && npm run build` — Vite 8.3.3 production build completed. Exact frontend versions are locked; engines require Node >=22.12.
- Headless Chromium against the local FastAPI service and Vite frontend checked primary successful requests, unsupported/empty results, failed-network handling and recovery, a 390px mobile viewport without horizontal overflow, and zero page errors.
- README screenshot regenerated from the running application and visually inspected.
- Python resolved dependencies are recorded in `backend/requirements.lock.txt`. No remote CI run is claimed.
- Delayed POST regression: `scripts/check-pending-inputs.cjs` failed before the pending-input fix and passed afterward. Both question and ingestion forms protect drafts while pending and re-enable afterward.
