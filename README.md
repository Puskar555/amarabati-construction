# Amarabati Construction — local website starter

**Domain reserved for future configuration:** `amarabati.com.np`  
**Source guide:** `Ammarawati_Construction_Platform_Architecture_Guide.pdf` (October 2026)  
**Release:** development MVP 0.1 — not production-ready

This is a working, local-first implementation of the initial architecture. It has three independent browser sites sharing one Python/FastAPI backend and **one private PostgreSQL database**. The frontend uses lightweight, dependency-free HTML/CSS/JavaScript for a faster inspectable first version; the PDF's proposed Next.js/NestJS structure remains a possible future migration, not a claim about this codebase.

The UI uses the `Amarabati` spelling consistent with the intended domain. Confirm the legal name and brand before launch.

## What you get now

| Component | URL | Included |
|---|---|---|
| Customer storefront | http://localhost:3000 | Homepage, catalog, search, product details, guest cart, login/registration, order or quotation **requests**, account history, privacy choices, materials guides |
| Land concept planner | http://localhost:3000/plan | Residential/commercial form, rectangular plot dimensions, **illustrative** room-zoning SVG, project saving |
| Super Admin | http://localhost:3001 | MFA sign-in, overview, products, operator rate proposals, independent rate approvals, requests, audit events |
| Regional Admin | http://localhost:3002 | MFA sign-in, territory-filtered overview, regional rates and requests |
| Backend API | internal only, via `/api/` on each site | HTTP-only session cookies, CSRF checks, role/region permissions, validated events, consent, order requests, PostgreSQL queries |
| PostgreSQL | private Docker network + `127.0.0.1:5433` for operator access | Users, sessions, catalog, operator rate versions, analytics, order requests, projects, audits |

**Important:** payments are **not** collected, checkout is an order/quote request only, stock is not managed, and initial product data has **no fabricated prices**. Prices appear only after a verified operator enters a rate and a *different* Super Admin approves it. The land plan is not a legal permit or engineered drawing.

## Local installation (recommended)

Requirements: Docker Desktop or Docker Engine with Compose V2, Python 3.11+ for key generation, and a modern browser. A suitable operating system with virtualization available is required.

```bash
cd amarabati-platform
python scripts/init_env.py
# Creates a private .env with separate random owner and application database passwords,
# signing key, and TOTP encryption key.
docker compose up --build -d
docker compose ps
curl http://localhost:3000/api/health
```

The health endpoint must respond with `{"status":"ok","database":"postgresql"}` before real registration and checkout requests will work.

Open the three URLs in the table above. On first start, PostgreSQL initializes from `db/schema.sql` and `db/seed.sql`. Seed data contains generic material *examples*, not supplier-confirmed stock or prices.

### Create admin accounts (no default accounts)

Provision a named Super Admin, then a second named Super Admin for independent price approval, plus a Regional Admin if desired:

```bash
docker compose exec api python -m app.cli --email owner@example.com --name "Head Office Owner" --role super_admin
docker compose exec api python -m app.cli --email approver@example.com --name "Rate Approver" --role super_admin
docker compose exec api python -m app.cli --email regional@example.com --name "Kathmandu Operator" --role regional_admin --region Kathmandu
```

For each account, the CLI prompts for a unique password (12+ characters) and prints a random TOTP secret **once**. Register it manually in your authenticator app (TOTP/30-second/6-digit). Never share it or commit it. Admin login requires both password and the current code. Replace sample addresses with real ones before provisioning.

**Test the price workflow:** sign in as a regional administrator, propose a price for `Kathmandu` with source notes. Sign in to Super Admin as a *different* person, approve the proposal. Refresh the storefront. Published product prices now come from PostgreSQL. The person proposing a rate cannot approve the same rate.

### Stop and back up

```bash
docker compose logs -f api       # observe application output
docker compose logs -f db        # database diagnostics
docker compose down             # stops services, preserves data volume
sh scripts/backup.sh            # produces local PostgreSQL custom-format dump
```

Avoid `docker compose down -v` unless you deliberately want to **erase all stored PostgreSQL records**. Database initialization scripts run only against a new empty data volume. Subsequent schema changes need reviewed SQL migration scripts; changing `schema.sql` is **not** a production migration.

Treat backups as sensitive customer data. Encrypt them and keep tested recovery copies in a separate secure location.

## Design-only preview without Docker

If you cannot run Docker yet, use:

```bash
python scripts/preview.py --site store --port 3000
# or: --site super --port 3001
# or: --site regional --port 3002
```

This is **read-only frontend preview mode**; the product catalog falls back to clearly labelled generic fixture data. It is not a substitute for PostgreSQL and cannot register customers, persist projects, execute checkout requests, or authenticate admin users.

## Where the code lives

```
apps/store/            Public e-commerce + planning frontend
apps/super/            Super Admin frontend
apps/regional/         Regional Operations frontend
apps/shared/           Shared frontend styles, API client, data validators
backend/app/main.py    Versioned HTTP API and role/region enforcement
backend/app/security.py Password hashes, TOTP, event validation
backend/app/costs.py   Basic cost/plot safety boundaries
backend/app/cli.py     Named admin provisioning with TOTP setup
db/schema.sql          Private PostgreSQL schema
db/seed.sql            Example product metadata (no prices)
deploy/nginx/site.conf Same-origin reverse proxy and browser security headers
compose.yaml           Local five-container topology
tests/                 Unit and source-contract security checks
docs/                  Product map, hardening plan and unresolved items
```

## Development and debugging checks

```bash
python -m compileall -q backend/app
pytest -q
node --check apps/store/app.js
node --check apps/shared/client.js
node --check apps/shared/admin.js
docker compose config
curl -i http://localhost:3000/api/health
```

Request responses include an `X-Request-ID` header to correlate support reports. The API never returns exception tracebacks to browser users. Check `docker compose logs -f api` for actual local errors. Do **not** store credentials in logs. The dashboard shows actual server records only; no invented commercial statistics are included.

The test suite validates password hashing, TOTP behavior, event field allowlists, regional authorization defaults, preview non-approval, no invented costs, and infrastructure source checks. **A live PostgreSQL integration suite, payment webhook tests, browser end-to-end tests, load tests, and professional penetration testing are still needed before launch.**

## Deploying `amarabati.com.np` later

Use these names as the planned deployment model; nothing is connected or deployed now:

- `amarabati.com.np` — public storefront
- `admin.amarabati.com.np` — Super Admin (strong access restrictions)
- `regional.amarabati.com.np` — Regional Operations Admin

Move the PostgreSQL primary into a private cloud subnet in a **company-owned** account. Keep it non-public. Require HTTPS/TLS, `COOKIE_SECURE=true`, approved production origins, a trusted WAF/CDN, separated identities and infrastructure administrator permissions, backups and an incident plan. See [docs/SECURITY.md](docs/SECURITY.md).

## What is deliberately not finished

- A gateway for **real payments**, settlement, taxes, shipping rates, stock reservations, invoice numbering, returns, refunds.
- Supplier catalogs and verified product specs, local inventory and actual region-dependent operator price data.
- Nepal municipality rules and verified bylaws, measured CAD plans, structural analysis, code-compliant designs or construction-ready drawings.
- AI model integration, tool permissions, document retrieval and model evaluation. These must be behind a replaceable AI gateway.
- Password-reset email verification and account recovery, customer export/erasure flows, lawful-retention policies and approved privacy/legal copy.
- Production MFA lifecycle (recovery, lost device procedures), CI security scanners, production secrets manager, edge DDoS/WAF, incident alerting, tested cloud backup recovery.
- Professional security sign-off, deployment-domain ownership confirmation and legally required business/compliance registrations.

**Do not advertise the website as secure against all attacks, ready to accept payments, or able to certify engineering decisions.**

## Suggested next milestone

Connect a real reviewed supplier catalog and approved local pricing, choose a Nepal payment/shipping integration, complete persistent cart & stock reservation, and test full transactions against PostgreSQL. Keep the external LLM optional until the approved construction rules and material knowledge base are reliable.
