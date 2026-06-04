# DEMO FILES — DELETE BEFORE PRODUCTION DEPLOYMENT

These files simulate accelerated sensor readings for demonstration purposes only.
They are **not** part of the production system.
Main production code never imports from this folder.

---

## Contents

| File | Purpose |
|------|---------|
| `simulate_demo.py` | Demo cooling simulation logic |
| `__init__.py` | Package marker (do not import in production) |

---

## How to use (demo only)

Start the server, then call:

```
POST https://localhost:5000/api/demo/cooling-run
```

This starts a fast 3-cycle cooling demo.
Each cycle drops from 87°C to 35°C in ~13 seconds (vs ~2 hours real-time).
The LOW threshold alert fires when temperature crosses 40°C.

To stop the demo early:

```
POST https://localhost:5000/api/demo/reset
```

---

## DELETE THIS FOLDER BEFORE PRODUCTION DEPLOYMENT.
