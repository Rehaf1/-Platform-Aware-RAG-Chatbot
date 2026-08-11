# APTWatch — Knowledge Base Admin

A real React + Vite admin console for the INT-AI-01 backend: upload documents,
watch them move through the ingestion pipeline, manage what's indexed, and
review questions the system couldn't answer.

## Setup

```bash
npm install
cp .env.example .env
npm run dev
```

Open the URL Vite prints (usually `http://localhost:5173`).

## Before it'll actually work: enable CORS on the backend

This app runs on a different origin (`localhost:5173`) than your FastAPI
backend (`127.0.0.1:8000`), so the browser will block requests unless the
backend explicitly allows it. Add this to `app/main.py`, near the top,
right after `app = FastAPI(...)`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Restart your backend after adding this.

## Getting a token

There's no login screen yet — paste a real admin JWT into the sidebar's
"Admin token" field. Generate one the same way you have all along:

```bash
python -c "
from dotenv import load_dotenv
load_dotenv('.env')
from app.auth.jwt_auth import create_access_token
print(create_access_token(platform_id='imtithal', tenant_id='demo_tenant', user_id='admin_1', user_role='admin'))
"
```

The token is stored in your browser's localStorage so it survives a refresh
during a work session — it's never sent anywhere except your own backend.

## Project structure

```
src/
  api/client.js         — all backend calls live here, one place
  components/
    Sidebar.jsx          — nav + token input
    PipelineTrail.jsx     — the upload-progress indicator
    StatusBadge.jsx       — colored status pill (indexed/processing/failed)
    UploadPanel.jsx       — the upload form
    DocumentTable.jsx     — real document list (GET /api/v1/documents)
    UnansweredQuestions.jsx
    FrequentlyAsked.jsx
  App.jsx                — layout + tab switching
  index.css              — design tokens (Tailwind v4 @theme)
```

## What's not built yet

- No real login — the token field is a stand-in until the backend has one
- No pagination on the document table (fine at current scale, worth adding
  if the list grows past what fits on screen)
- Build with `npm run build`, output lands in `dist/` — not yet wired into
  Docker or served by the backend itself
