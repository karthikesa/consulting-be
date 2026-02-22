# Rathinam – FastAPI + PostgreSQL

This project uses **FastAPI** and connects to your PostgreSQL database named **mobile** (user: systemiser).

---

## What you need first

1. **PostgreSQL** must be installed and running on your Mac.
2. The database **mobile** must exist, and the user **systemiser** must be able to connect to it (with password: systemiser).

To connect with `psql` from the terminal:

```bash
psql -U systemiser -d mobile
# When asked, enter password: systemiser
```

---

## Step 1: Open terminal in the project folder

In Cursor, open the terminal (Terminal → New Terminal) and go to this project:

```bash
cd /Users/karthik_eswaran/workspace/rathinam
```

---

## Step 2: Create a virtual environment (recommended)

This keeps project packages separate from the rest of your system:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` at the start of the line. That means the virtual environment is active.

---

## Step 3: Install FastAPI and database packages

With the virtual environment active, run:

```bash
pip install -r requirements.txt
```

This installs FastAPI, Uvicorn (the server), SQLAlchemy, the PostgreSQL driver, and python-dotenv.

---

## Step 4: Run the FastAPI app

Start the server:

```bash
uvicorn main:app --reload --host 0.0.0.0
```

You should see something like: `Uvicorn running on http://127.0.0.1:8000`

- **API docs (Swagger):** open in browser: http://127.0.0.1:8000/docs  
- **Health check:** http://127.0.0.1:8000/health  
- **Database check:** http://127.0.0.1:8000/db-check  

If `/db-check` returns `"database": "connected"`, the app is talking to your **mobile** database correctly.

---

## Project layout

- **app/** – Main application package  
  - **app/database.py** – PostgreSQL connection, engine, Base, mixins  
  - **app/core/** – Config and security (JWT, password hashing)  
  - **app/auth/** – JWT auth: models, schemas, routes, service, dependencies  
- **app/vehicles/** – Vehicle listings (car, bike, EV) with image upload, multi-tenant  
- **alembic/** – Database migrations  
- **storage/vehicles/** – Uploaded vehicle images  
- **scripts/seed_defaults.py** – Seeds default account and role after migrations  
- **main.py** – FastAPI app entry (includes auth router)

---

## Database migrations (Alembic)

All DB changes are done via migration files, not by hand.

**First-time setup (create auth tables):**

```bash
alembic upgrade head
python -m scripts.seed_defaults
```

**After changing models (add a new table or column):**

```bash
alembic revision --autogenerate -m "Describe your change"
alembic upgrade head
```

**Useful commands:**

- `alembic current` – Show current revision  
- `alembic history` – List revisions  
- `alembic downgrade -1` – Undo last migration  

Migrations use the same DB URL as the app (from `.env`).

---

## Changing database settings

Database connection is read from a `.env` file in the project folder. Create it from the example:

```bash
cp .env.example .env
```

Then edit `.env` and set **DB_PASSWORD** (and optionally DB_USER, DB_NAME, etc.) to match your actual PostgreSQL setup. The app and Alembic both use this file.

---

## Troubleshooting: "password authentication failed for user"

If you see **password authentication failed for user "systemiser"** when running `alembic upgrade head` or starting the app:

1. **Set the correct password in `.env`**  
   Create a file named `.env` in the project root (or copy from `.env.example`) and set:
   ```bash
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=mobile
   DB_USER=systemiser
   DB_PASSWORD=the_password_you_use_for_psql
   ```
   Use the **exact same password** you type when you run `psql -U systemiser -d mobile`.

2. **Check that PostgreSQL accepts that user and password**  
   In a terminal, run:
   ```bash
   psql -U systemiser -d mobile
   ```
   When prompted, enter the password. If this fails, the app will fail too. Fix the user/password in PostgreSQL first (see step 3).

3. **If the user or database doesn’t exist, create them in PostgreSQL**  
   Connect as a superuser (e.g. your Mac user or `postgres`), then:
   ```sql
   CREATE USER systemiser WITH PASSWORD 'your_chosen_password';
   CREATE DATABASE mobile OWNER systemiser;
   ```
   Then put that same password in `.env` as **DB_PASSWORD**.

---

## Vehicles API

After running `alembic upgrade head`, vehicle endpoints are available:

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | /vehicles/browse | No | List active vehicles (paginated, filter by product) |
| GET | /vehicles/browse/{id} | No | Get single active vehicle |
| GET | /vehicles | Yes | List vehicles for logged-in user's account |
| POST | /vehicles | Yes | Create vehicle with multiple images (multipart/form-data) |
| GET | /vehicles/{id} | Yes | Get vehicle (own account only) |
| PATCH | /vehicles/{id} | Yes | Update vehicle |
| POST | /vehicles/{id}/images | Yes | Add images |
| DELETE | /vehicles/{id}/images | Yes | Remove images (body: `{"image_ids": [1,2]}`) |
| DELETE | /vehicles/{id} | Yes | Delete vehicle and images |

**Image URLs:** `image_path` in responses is relative. Full URL: `{API_BASE}/storage/{image_path}` (e.g. `http://localhost:8000/storage/vehicles/abc123.jpg`).

---

## Next steps

- Run migrations: `alembic upgrade head` then `python -m scripts.seed_defaults`.
- Use auth endpoints from your mobile app (register, login, then send `Authorization: Bearer <access_token>`).
- Add new API routes under `app/` and protect them with `Depends(get_current_user)` from `app.auth.dependencies`.
- When you change models, create a new migration with `alembic revision --autogenerate -m "message"` then `alembic upgrade head`.
