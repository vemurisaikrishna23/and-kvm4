# Running the ATD Backend

Django 5.2 + DRF + Channels. All commands run from `backend/atd/` unless stated otherwise.

---

## Quick start

```bash
cd backend/atd
source ../../env/bin/activate
daphne -b 0.0.0.0 -p 8000 atd.asgi:application
```

Or from the repo root, which does all three and prints the URLs:

```bash
./run-wsl.sh          # defaults to port 8000
./run-wsl.sh 8080     # or pick a port
```

> **Use `daphne`, not `runserver`.** This app serves WebSockets, which need ASGI.
> `python manage.py runserver` is WSGI-only — HTTP will look fine while every
> WebSocket silently fails. `WSGI_APPLICATION` is commented out in `settings.py`
> for exactly this reason.

---

## URLs

| What | URL |
|---|---|
| Swagger docs | http://localhost:8000/api/docs/ |
| ReDoc | http://localhost:8000/api/redoc/ |
| OpenAPI schema | http://localhost:8000/api/schema/ |
| Django admin | http://localhost:8000/admin/ |
| API root | http://localhost:8000/api/ |
| WebSocket | `ws://localhost:8000/ws/dispenser-control/?imei_number=<IMEI>&token=<TOKEN>&client_type=hardware\|web` |

---

## First-time setup

```bash
cd backend/atd
python3 -m venv ../../env
source ../../env/bin/activate
pip install -r requirements.txt
```

`mysqlclient` needs system libraries. On Ubuntu/WSL:

```bash
sudo apt update
sudo apt install -y build-essential python3-dev default-libmysqlclient-dev pkg-config
```

---

## Everyday commands

```bash
# Sanity-check settings, URLs and models without starting the server
python manage.py check

# Open a Python shell with Django loaded
python manage.py shell

# Open a MySQL client against the configured database
python manage.py dbshell

# Rebuild static files (needed for admin / Swagger CSS in production)
python manage.py collectstatic --noinput

# Print the OpenAPI schema to a file
python manage.py spectacular --file schema.yml
```

---

## Migrations

`IoT_Panel` owns all 12 of its tables — migrate it freely.

`existing_tables` holds 92 models mirroring the Laravel app that shares this
database. 91 are `managed = False`, so Django reads and writes their rows but
will never create or alter them. **Always name the app explicitly** so a stray
`makemigrations` can't touch them:

```bash
python manage.py makemigrations IoT_Panel      # not bare `makemigrations`
python manage.py migrate

# Inspect before applying
python manage.py showmigrations IoT_Panel
python manage.py sqlmigrate IoT_Panel 0024
```

> **One exception.** `DeliveryLocations` (`delivery_locations`) is `managed = True`
> and Django does own its schema — see `existing_tables/migrations/0003` and `0004`.
> Editing that model generates real `ALTER TABLE`s against a table Laravel also
> uses, so coordinate before changing it.

---

## Docker

```bash
cd backend/atd
docker build -t atd-backend .
docker run -d --name atd-backend -p 8000:8000 atd-backend

docker logs -f atd-backend
docker stop atd-backend && docker rm atd-backend
```

Pushing to `main` triggers `.github/workflows/main.yml`, which builds the image,
pushes it to Docker Hub as `myaccess2021/atd-backend:latest`, and redeploys it
over SSH on port **8003**.

---

## Reaching the server from the LAN (WSL only)

WSL2 gets a fresh IP on every reboot, so the port forward must be re-run.
From an **elevated** PowerShell at the repo root:

```powershell
.\expose-wsl.ps1 -Port 8000            # forward
.\expose-wsl.ps1 -Port 8000 -Remove    # tear down
```

It prints the LAN URLs to hand out. Add any new host to `CORS_ALLOWED_ORIGINS`
and `CSRF_TRUSTED_ORIGINS` in `atd/settings.py` or the browser will block it.

---

## External services

Both are remote and configured in `atd/settings.py` — nothing runs locally.

| Service | Used for | Fails as |
|---|---|---|
| MySQL (AWS RDS) | all data | server won't start / 500s |
| Redis | Channels layer | HTTP fine, WebSockets drop |

Quick reachability check:

```bash
python manage.py dbshell -- -e "SELECT 1;"      # MySQL
redis-cli -u redis://:<password>@178.16.137.196:6379/0 ping   # expect PONG
```

---

## Troubleshooting

| Symptom | Cause |
|---|---|
| WebSockets never connect, HTTP is fine | Started with `runserver` instead of `daphne`, or Redis unreachable |
| WS closes with `4001` | Token invalid or doesn't match the IMEI |
| WS closes with `4002` | `client_type` is not `hardware` or `web` |
| WS closes with `4003` | IMEI not assigned to a dispenser mapping |
| `SynchronousOnlyOperation` | ORM called from async code without `@database_sync_to_async` |
| Swagger loads unstyled | Run `collectstatic`; WhiteNoise serves those files |
| `ModuleNotFoundError: drf_spectacular` | Wrong venv, or `pip install -r requirements.txt` not run |
| CORS / CSRF errors from the frontend | Origin missing from `CORS_ALLOWED_ORIGINS` / `CSRF_TRUSTED_ORIGINS` |

---

## Layout

```
backend/atd/
├── manage.py
├── atd/                 # project config
│   ├── settings.py      # DB, Redis, CORS, Swagger
│   ├── urls.py          # HTTP routes
│   └── asgi.py          # entry point: HTTP + WebSocket split
├── IoT_Panel/           # the application
│   ├── models.py        # 12 owned tables
│   ├── views.py         # APIView per endpoint
│   ├── serializers.py   # validation + shaping
│   ├── urls.py          # /api/... routes
│   ├── consumers.py     # WebSocket protocol
│   └── routing.py       # /ws/... routes
└── existing_tables/     # 92 Laravel tables — 91 unmanaged, read/write only
```
