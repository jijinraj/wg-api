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
