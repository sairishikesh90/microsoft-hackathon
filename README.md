# SafeRoute AI

A disaster-aware route safety MVP.

## Current flow

User location
-> Destination
-> Hazard data
-> Risk calculation
-> Route safety
-> Safer route recommendation

## Current MVP limitations

- Uses demo hazard records.
- Uses geometric demo routes rather than live road routing.
- Does not yet connect to live government APIs.
- Hindsight integration is intentionally a later phase.

## Run backend

```bash
cd backend
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install:

```bash
pip install -r requirements.txt
```

Start:

```bash
uvicorn main:app --reload
```

Backend:
http://127.0.0.1:8000

API docs:
http://127.0.0.1:8000/docs

## Run frontend

From the frontend folder:

```bash
python -m http.server 5500
```

Open:

http://127.0.0.1:5500
