# API Overview — AcademIA

> FastAPI backend at :8000. Auto-generated docs available at `/docs` (Swagger) and `/redoc`.

## Authentication

JWT-based. Login returns access_token + refresh_token.

```
POST /api/auth/login
Body: {"username": "...", "password": "..."}
Response: {"access_token": "...", "refresh_token": "...", "token_type": "bearer"}
```

All protected endpoints require: `Authorization: Bearer <access_token>`

## Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/auth/login | Authenticate user |
| GET | /api/me/concepts | Learner's concept scores + level |
| GET | /api/me/streaks | Current streak + history |
| GET | /api/me/xp | XP total + level |
| POST | /api/chat | Proxy to Dify Teacher (SSE streaming) |
| PATCH | /api/settings/mode | Toggle structured/free mode |
| GET | /api/health | Health check |

## Chat streaming

The `/api/chat` endpoint proxies to Dify's chat-messages API with SSE streaming:

```
POST /api/chat
Headers: Authorization: Bearer <token>
Body: {"message": "What's the difference between since and for?"}
Response: SSE stream (text/event-stream)
```

Each SSE event contains a token from the LLM response. The frontend renders them in real-time.

## Rate limiting

In-memory per-IP rate limiter. Configurable in FastAPI middleware.
