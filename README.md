### Local run (Windows PowerShell)

1. Create venv + install:

```
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -U pip
   pip install -e .
```

2. Set env (or create .env and load however you like):

```
$env:DATABASE_URL="postgresql+asyncpg://wg:wgpass@localhost:5432/wg"
$env:JWT_SECRET="CHANGE_ME_NOW"
$env:ALLOW_MEMORY_USERS="true"
```

3. Init DB tables:

```
python .\src\app\scripts\init_db.py
```

4. Run API (from project root):

```
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

```

5. Swagger:http://localhost:8000/docs

```
## .env.example
env
JWT_SECRET=CHANGE_ME_NOW
DATABASE_URL=postgresql+asyncpg://wg:wgpass@localhost:5432/wg
ALLOW_MEMORY_USERS=true
CORS_ORIGINS=*
```

## Backend Architecture (Quick Guide)

This backend is organized by modules to keep things clean and scalable.

### Key layers

- **Routers** (`modules/*/router.py`): Define API endpoints (HTTP), call service functions, return responses.
- **Services** (`modules/*/service.py`): Business logic + database operations (select/insert/update/delete).
- **Schemas** (`modules/*/schemas.py`): Pydantic models defining request/response JSON formats.
- **DB Models** (`db/models.py`): SQLAlchemy ORM table definitions (User, Peer, etc.).
- **DB Session** (`db/session.py`): Creates an async SQLAlchemy session per request.
- **Security** (`core/security.py`): JWT token generation + auth dependencies (`get_user`, `require_admin`).
- **Config** (`core/config.py`): Environment-based settings + static constants (LOCATIONS).
- **Init Script** (`scripts/init_db.py`): Creates tables from models (dev convenience; migrations later).

### Adding a new feature

1. Add/update schemas in `modules/<module>/schemas.py`
2. Implement logic in `modules/<module>/service.py`
3. Add the endpoint in `modules/<module>/router.py`
4. If needed, update DB models in `db/models.py` and apply DB changes
5. Protect endpoints using:
   - `Depends(get_user)` for logged-in routes
   - `Depends(require_admin)` for admin-only routes

Rule of thumb: **router = HTTP**, **service = logic**, **schemas = JSON shapes**, **models = DB tables**.
