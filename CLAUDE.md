# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

This project uses `uv` for dependency management (Python 3.14).

```bash
# Run the development server
uv run uvicorn main:app --reload

# Run database migrations
uv run alembic upgrade head

# Generate a new migration after changing models.py
uv run alembic revision --autogenerate -m "description of change"

# Roll back one migration
uv run alembic downgrade -1
```

## Architecture

This is a **flat-structured FastAPI backend** — all application code lives in the project root with no subdirectories.

| File | Purpose |
|---|---|
| `main.py` | FastAPI app instance, all route handlers, and the `get_current_user` auth dependency |
| `models.py` | SQLAlchemy ORM models (`User`, `Note`, `NoteShare`) |
| `schemas.py` | Pydantic schemas for request validation and response serialization |
| `database.py` | Engine setup, `SessionLocal`, `Base`, and the `get_db` dependency |
| `utils.py` | Password hashing (raw bcrypt) and JWT creation/verification |
| `alembic/` | Alembic migration environment; `versions/` holds migration scripts |

### Data Model

- **User** owns many **Notes** (cascade delete on user removal)
- **Note** has many **NoteShares** (cascade delete on note removal)
- **NoteShare** links a Note to another User with a `PermissionLevel` enum (`VIEW`, `EDIT`, `FULL`)

### Auth Flow

1. `POST /users/register` — creates user with bcrypt-hashed password
2. `POST /users/login` — validates credentials, returns JWT (`access_token`)
3. Protected routes use `Depends(get_current_user)` in `main.py`, which decodes the JWT and queries the user from DB

The `oauth2_scheme` uses `tokenUrl="users/login"`, and the JWT payload stores the user's email as the `"sub"` claim.

### Database

- PostgreSQL hosted on **Neon** (serverless). The connection string is in `.env` as `DATABASE_URL`.
- `pool_pre_ping=True` is set in `database.py` to handle Neon's cold-start behaviour.
- Alembic reads `DATABASE_URL` from `.env` via `alembic/env.py`.

### Adding New Features

When adding new models: define in `models.py`, add Pydantic schemas to `schemas.py`, add routes to `main.py`, then run `alembic revision --autogenerate`.

When adding protected endpoints: use `current_user: models.User = Depends(get_current_user)` as a parameter.
