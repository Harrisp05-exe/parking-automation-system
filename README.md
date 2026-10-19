# Parkflow — Java + Django parking automation

A Java Swing desktop form takes driver name, number plate, car model and color. Django assigns the first available spot, records server entry time, and returns a private parking-pass URL. Java opens this URL in your default browser. The map shows available, occupied and your assigned space, refreshing every five seconds. Checkout records server exit time, releases the spot, and generates a printable bill.

Defaults: **24 spaces, INR 50 per started hour, minimum one hour**. An exact 60-minute visit costs INR 50; 60 minutes plus any fraction costs INR 100. Rates and currency are saved on each visit so later configuration changes do not change an existing visit's rate. Billing is calculated on the server. This generates a bill; it does not process payment. Physical occupancy is based on check-in and checkout, not sensors or cameras.

## Quick start (Windows PowerShell)

Requires Python 3.12 and JDK 17+. Open a terminal in this project directory:

```powershell
.\setup.ps1
.\.venv\Scripts\python.exe manage.py runserver
```

In a second terminal in this directory:

```powershell
.\java\run-kiosk.ps1
```

Fill the four fields and press Enter. Your browser opens the assigned space. Keep that private URL to check out later. The kiosk's **Next vehicle** button resets the form; it does not check out the previous car. The public map is at http://127.0.0.1:8000/ and intentionally excludes personal details.

If PowerShell script execution is restricted, run these commands individually:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_spots --count 24
.\.venv\Scripts\python.exe manage.py runserver
# In another terminal:
javac -encoding UTF-8 java/ParkingKiosk.java
java -cp java ParkingKiosk
```

Linux/macOS: use `python3 -m venv .venv`, `.venv/bin/python` in place of the Windows Python path, and `cp .env.example .env`. Java commands are the same. The virtual environment is machine-specific and is recreated by setup; it is not included in the source ZIP.

## Vercel deployment

**Deploy the Django server to Vercel. Run the Java desktop kiosk locally.** A desktop Swing window cannot be hosted as a browser page. The kiosk can connect to your hosted Django server over HTTPS.

The project follows Vercel's Django auto-detection, using `manage.py`, `WSGI_APPLICATION`, Python 3.12 and collected static assets: https://vercel.com/docs/frameworks/full-stack/django

1. Put this project's contents in a Git repository and import it into Vercel. The root directory must contain `manage.py`. Use the Django framework preset/automatic detection. No frontend build or output-directory override is needed.
2. Provision a persistent PostgreSQL database (for example through Vercel's database marketplace). Use its PostgreSQL connection string as `DATABASE_URL`. Do not use the local SQLite file on Vercel.
3. Set these environment variables in the Vercel project:

   | Variable | Value |
   |---|---|
   | `DATABASE_URL` | PostgreSQL URL with SSL, preferably the provider's pooled connection URL |
   | `DJANGO_DEBUG` | `0` |
   | `DJANGO_SECRET_KEY` | Random secret, at least 40 characters |
   | `KIOSK_API_KEY` | Different random secret, at least 32 characters |
   | `DJANGO_ALLOWED_HOSTS` | Your production hostname, without scheme (e.g. `your-project.vercel.app`) |
   | `CSRF_TRUSTED_ORIGINS` | Your exact HTTPS origin (e.g. `https://your-project.vercel.app`) |
   | `PARKING_RATE` | `50.00` |
   | `PARKING_CURRENCY` | `INR` |

   Generate each secret separately with `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Do not commit secrets. Automatic Vercel deployment hostnames are also allowed by the settings.
4. Initialize the remote database once from your local virtual environment. Set `DATABASE_URL` in your local `.env` to the hosted PostgreSQL connection string with `?sslmode=require`, then run:

   ```powershell
   .\.venv\Scripts\python.exe manage.py migrate
   .\.venv\Scripts\python.exe manage.py seed_spots --count 24
   ```

   Use the appropriate database credentials locally. Migrations deliberately do not run on every request or automatically on every preview build. Use separate databases for preview and production. Restore your local `.env` afterward if you want SQLite locally.
5. Deploy/redeploy in Vercel. Static files are collected during build. Open the deployment and verify that 24 spaces appear.
6. Point the local Java kiosk at your deployment. In the terminal used to launch Java:

   ```powershell
   $env:PARKING_SERVER_URL='https://your-project.vercel.app'
   $env:KIOSK_API_KEY='your-matching-kiosk-secret'
   .\java\run-kiosk.ps1
   ```

   The key must match the server value. Java reads environment variables, not Django's `.env`. Use the production URL accessible to the kiosk; a Vercel preview login page will not work as the API endpoint.

Deployment configuration is included, but an actual deployment requires your Vercel account, database and secrets. No live deployment or payment gateway is included.

## Configuration and design

- Change rates/currency/time zone in `.env` locally or Vercel environment settings. Restart/redeploy after changes.
- `seed_spots --count 32` adds spots. It never deletes existing spaces or history; a smaller count does not shrink the lot.
- Database partial unique constraints prevent two active visits sharing one spot or one plate. Transactions and row locking coordinate PostgreSQL allocations. SQLite is intended for local demos; PostgreSQL is required for production concurrency.
- Each submission has an idempotency UUID. Retrying unchanged kiosk details returns the same pass after a lost response.
- Checkout requires POST and CSRF protection. Repeated checkout preserves the first exit time and bill.
- Private UUID pass URLs grant access to a visit and checkout. Treat them as bearer tickets; do not share them. This is a kiosk project without user accounts or a pass-recovery portal.
- The kiosk API key belongs on trusted operator machines. There is no API for exposing vehicle details in the public map.
- Spot labels are arranged in rows of eight: A01–A08, B01–B08, etc.

## Verification

```powershell
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
javac -encoding UTF-8 java/ParkingKiosk.java
```

Tests cover assignment, validation, authentication, private-pass rendering, billing boundaries, full capacity, space reuse, retry idempotency and CSRF-protected checkout. They use an isolated test database.
