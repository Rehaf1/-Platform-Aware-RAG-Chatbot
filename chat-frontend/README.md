# Chat Frontend

The end-user chat UI for the Platform-Aware RAG Chatbot (Person B / Read Path).
Talks to `POST /api/v1/chat` and `POST /api/v1/feedback` on the FastAPI backend.

## Setup

```bash
npm install
cp .env.example .env
# edit .env if your backend isn't on http://127.0.0.1:8000
npm run dev
```

Opens on `http://localhost:5174` by default (separate port from `admin-frontend`'s
5173, so both can run side by side during development).

## How auth works right now

There's no real login screen yet -- each APTWatch platform is expected to issue
its own JWT and hand it to this app (e.g. as a query param when embedding the
chat widget). Until that integration exists, `TokenGate` lets you paste a
token manually (generate one the same way you have been for testing:
`create_access_token(...)` in `app/auth/jwt_auth.py`).

## Conversation continuity

The backend never guesses whether a message continues a conversation --
the client decides. This app stores the `conversation_id` it gets back
from `/api/v1/chat` in `localStorage` and sends it on every subsequent
message. Clicking "New conversation" clears it, so the next message
starts a fresh conversation.

## Feedback

Each assistant message that was successfully saved to the database
carries a `message_id`. The thumbs up/down buttons under a message call
`POST /api/v1/feedback` with that id -- feedback is only accepted for
messages belonging to the requesting user's own conversations.
