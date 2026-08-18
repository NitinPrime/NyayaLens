# Security Model

## Principles

1. Uploaded legal documents are treated as **sensitive data**
2. Documents are **untrusted input** — never executed as instructions
3. No API keys in frontend code
4. No sensitive data in logs

## Authentication (Planned)

- JWT-based authentication
- Password hashing via bcrypt
- Case-level access control

## Input Validation

- Pydantic models validate all API inputs
- File upload size limits (configurable, default 25MB)
- MIME type validation
- Prompt injection resistance for document content

## Audit Logging

All sensitive operations logged to `audit_logs` table:

- Case creation, analysis, evidence upload
- No full document content in logs

## Environment Variables

All secrets via environment variables (see `.env.example`):

- `API_SECRET_KEY`
- `JWT_SECRET_KEY`
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`
- `DATABASE_URL`

## Rate Limiting (Planned)

- Per-user API rate limits
- Upload frequency limits

## Current Status

Database schema includes `users` and `audit_logs` tables. Authentication middleware not yet implemented.
