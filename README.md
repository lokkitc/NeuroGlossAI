# NeuroGlossAI

NeuroGlossAI is an AI-first language learning product.

This repository contains:

- **backend/** — FastAPI + SQLAlchemy (async) API
- **frontend/** — Flutter client

## Quick start (Docker)

1) Create `backend/.env` based on `backend/.env.example`.
2) From the repo root:

```bash
docker compose up --build
```

API:

- `http://localhost:8000/docs`
- `http://localhost:8000/api/v1/openapi.json`

Postgres (Docker):

- host: `localhost`
- port: `5433`

## Local development

- Backend docs: `backend/README.md`
- Frontend docs: `frontend/README.md`

## Configuration

- Backend env sample: `backend/.env.example`

Required backend variables:

- `DATABASE_URL`
- `SECRET_KEY`

## Security model (high-level)

- **Auth**: JWT access token + refresh token rotation (server-side stored refresh token hashes)
- **Rate limiting**: slowapi on login/refresh/logout and other sensitive endpoints
- **CORS**: configured origins; `*` is blocked in production
- **Uploads**: S3 uploads are **private by default**; API can return **presigned URLs** (short-lived)

### Uploads (S3) note

Presigned URLs expire. For S3 provider you can obtain a fresh URL via:

- `GET /api/v1/uploads/presign?public_id=...`

## Production checklist (minimum)

- **Secrets**
  - Set a strong `SECRET_KEY`.
  - Never commit `.env`.
- **CORS**
  - Set `BACKEND_CORS_ORIGINS` to exact frontend domains.
- **TLS**
  - Terminate HTTPS at a load balancer / reverse proxy.
- **Uploads**
  - Keep S3 uploads private (`S3_OBJECT_ACL` unset).
  - Use presigned URLs (`S3_RETURN_PRESIGNED_URL=true`).
- **Logging**
  - Ensure logs do not contain tokens, request bodies, or PII.
- **Rate limiting / WAF**
  - Keep slowapi enabled and add WAF / reverse-proxy throttling.
- **Database**
  - Run migrations (`alembic upgrade head`).
  - Configure backups.

## License

See `LICENSE`.
