# Build status — local MVP 0.1 (26 October 2026)

This is source code for **amarabati.com.np**, not a deployed production website. There are three independent frontend applications, one shared backend, and PostgreSQL as the **only** primary database. The original PDF architecture is included for reference.

## Implemented

- Storefront: responsive home, static SVG house illustration, categorization, full-text-like catalog filtering, generic sample product cards, details, guest cart, account forms, material guides, basic plot preview.
- Backend: catalog & operator-approved regional rate lookup, customer registration/login, scrypt passwords, session cookies, CSRF, TOTP for admins, country-region text scopes, activity event collector, consent preferences, projects, order/quote requests, basic admin analytics, audit events.
- Admin: two independent frontend sites; protected Super and Regional roles; regional filtering; rate proposal with independent approval; basic product addition and audit review.
- Security: private PostgreSQL + separate non-superuser app role; audit table append-only for app role; strict API origin checks and request schema validation; restrictive HTTP security headers; CSP; bearer-free cookie-based session design; signed analytics preference.
- Local deployment: Docker Compose PostgreSQL, API, nginx per site, env secret generator, first-run schema/seed, PostgreSQL backup script, read-only design preview.
- Testing: **12 passing automated tests** for auth helpers, role scoping, data boundaries, security headers, etc. JS syntax and Python compile tests pass. Desktop/mobile visual screenshot smoke tests pass with static preview fixtures.

## Integration tests not run in this execution environment

Docker Engine and a local PostgreSQL service were not present in the build environment. Therefore actual DB-backed sign-up, approval, order and session workflows have **not** been exercised against a running database here. Run `docker compose up --build -d` and a manual/automated live database test suite before treating the MVP as working end-to-end.

## Deferred in this version

- Real payment/paid orders, taxes, shipping, inventory, stock reservations, supplier systems and refunds.
- Professionally verified Nepal municipality setbacks/FAR and construction-ready architectural/structural drawings.
- Price ingestion from real suppliers; final engineered quantity takeoffs and genuine cost estimates.
- External LLM integration; model-agnostic AI Gateway remains an architectural target.
- Complete auth recovery, identity verification, data retention & erasure, regulatory/legal approvals.
- Penetration testing, production observability, WAF, separate cloud credentials/secrets vault, backup restore tests and multi-cloud deployment.

## Steps for first operator acceptance

1. Generate .env and run Compose; confirm `/api/health` and that seed products appear.
2. Register a customer and verify a session cookie with HttpOnly.
3. Add an unpriced material to cart; submit a quotation request while signed in; verify saved order status.
4. Provision two admins + one regional admin with TOTP; verify wrong OTP and regional access are denied.
5. Propose a rate, reject self-approval, and approve with a different Super Admin; verify regional price is visible.
6. Switch analytics to Essential Only and confirm optional events are not stored; consent and confirm allowed events.
7. Create and save a project; verify SVG is labelled unapproved.
8. Back up PostgreSQL, restore to a separate test database and validate row counts and permissions.
9. Run permission attack tests, input tests, dependency scan, browser E2E and independent security review before launch.
