# Shohay (সহায়) — Backend API

FastAPI backend for Shohay, a flood-relief coordination platform for Bangladesh. It serves the
React frontend in the `Shohoy` repository.

- **Citizens** request help without an account and track it with a tracking ID.
- **Coordinators** (admins) verify requests, dispatch them to volunteers, manage warehouse stock
  and watch drones.
- **Field volunteers** accept tasks, log duty hours and respond to drone alerts.
- **Drones (UAV module)** — merged from the ResQTech FYDP backend — report heartbeats and
  detections of stranded people; a coordinator turns a detection into a normal rescue request.

API docs are generated automatically at `/docs` (Swagger) and `/redoc`.

## Run it locally (no production access needed)

```bash
pip install -r requirements.txt
python main.py            # http://127.0.0.1:8000/docs
```

With `SUPABASE_DB_URL` empty (or no `.env` at all) the app uses a local SQLite file
(`shohay_local.db`) that is created and filled with demo data on first start:

| Demo user (local only) | id | role |
|---|---|---|
| District Coordinator | `usr-admin-001` | admin |
| Nasrin Akter | `usr-field-001` | fieldworker |
| Rahim Ahmed | `usr-public-001` | public |

A demo drone `DEMO-UAV-01` (key `local-demo-drone-key`) is seeded too. Delete `shohay_local.db`
to start fresh.

## Tests

```bash
python test_flows.py         # the whole journey: request -> dispatch -> volunteer -> resolved, drones, auth
python test_api.py           # every endpoint
python test_supabase_orm.py  # the data layer on SQLite
```

All three run against throwaway SQLite databases and never touch production.
`SHOHAY_TEST_DB_URL=<empty disposable Postgres with the migration applied> python test_flows.py`
runs the flow test on PostgreSQL.

## Drone simulator (demo without hardware)

```bash
python main.py                                  # terminal 1
python scripts/simulate_drone.py                # terminal 2: seeded demo drone
python scripts/simulate_drone.py --api https://<backend> --drone-id SUN-UAV-02 --token <key from the UAV Monitor>
```

## Environment variables

| Variable | Needed for |
|---|---|
| `SUPABASE_DB_URL` | Production database (Supabase pooler URI). Empty = local SQLite. |
| `SUPABASE_URL` | **Required in production** — used to verify Supabase sign-in tokens. |
| `ADMIN_EMAILS` | Comma-separated emails that become coordinators when they sign in. |
| `ALLOW_LEGACY_AUTH` | `false` (default). `true` re-enables the old unverified login endpoints — tests only. |
| `SECRET_KEY` | Signs the backend's own (legacy) tokens. |
| `RESEND_API_KEY`, `RESEND_FROM_EMAIL` | Only for the legacy email-OTP endpoints. |

## Database changes

Schema changes live in `migrations/` as idempotent SQL. Apply them **before** deploying code
that needs them:

```bash
python scripts/migrate.py   # shows the target database and asks for "yes"
```

(or paste the file into Supabase → SQL Editor). `001_flow_uav_rls.sql` adds the volunteer-flow
columns, warehouse movements, the UAV tables, and turns on Row Level Security so the public
Supabase REST API cannot read or change any table. The backend connects as the table owner and
is not affected.

## Deploy checklist (Vercel)

1. Run the migration on Supabase (above).
2. Set `SUPABASE_DB_URL`, `SUPABASE_URL`, `ADMIN_EMAILS`, `SECRET_KEY` in Vercel.
3. Deploy the backend, then the frontend.

## Code map

```
main.py                 app, CORS, router registration
config.py               all settings (from .env / environment)
routers/                one file per area: requests, volunteers, warehouse, uav, auth, ...
routers/deps.py         who is calling: get_current_user, require_roles, get_current_drone
schemas/                request/response shapes (Pydantic) — what the API accepts and returns
database/models.py      tables (SQLAlchemy)
database/repository.py  every read/write for the main tables
database/uav_repository.py  drones, detections, rescuer links, audit log
database/seed.py        demo data for the local SQLite database
services/otp_service.py token verification (Supabase JWKS + legacy tokens)
migrations/             SQL for the production database
scripts/                migrate.py, simulate_drone.py
```
