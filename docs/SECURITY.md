# Security, sabotage resilience and debugging plan

## Protections in the local source today

- Private PostgreSQL service with separate owner and least-privilege application DB roles, and a host-mapped port restricted to `127.0.0.1` (not an internet-facing DB).
- Parameterized SQL for queries and rate/version writes; input validation through Pydantic and bounded API data.
- Passwords hashed using salted scrypt; no shipping/default administrator passwords.
- Named Super and Regional administrators with mandatory TOTP MFA and AES-GCM-encrypted TOTP secrets (environment-managed symmetric key).
- Random cryptographic session tokens; only hashed session token identifiers retained server-side; HttpOnly SameSite cookies; 12-hour expiry, logout revocation.
- Cookie-bound CSRF protection on authenticated modifications, plus origin and cross-site checks. Same-origin frontend API proxy.
- Browser CSP, frame-ancestors denial, no-sniff, referrer restrictions, device permission restrictions.
- Backend authorization on every admin endpoint, including fail-closed exact region scoping for regional operations.
- Two-person approval of material rates: a proposer cannot approve their own entry.
- Event type and field allowlist, signed consent preference, analytics opt-in, bounded event data, deletion of visitor events upon consent withdrawal.
- Transactions for order lines and totals recomputed from the current approved **server** rates; status explicitly acknowledges no payment integration.
- Append-only audit entries (runtime app DB role cannot update/delete audit rows) for logins, admin price decisions, product creation, orders and projects; request IDs for debugging.
- Local rate limiting (in-memory per API process), no default cross-origin API permissions, non-root API process in Docker.

These are **baseline engineering protections**, not proof of full security or protection against all sabotage.

## Required before any internet-facing release

1. HTTPS with HSTS after the hostname is verified; `COOKIE_SECURE=true`; strict allowed origins; audited host/proxy forwarding configuration.
2. Fix and test production session isolation for `admin.` and `regional.` subdomains, administrator step-up authentication and privileged role lifecycle.
3. Add a distributed rate limiter and edge DDoS/WAF; monitor abuse against registration, login, order and search endpoints.
4. Enforce email verification, safe account recovery, breached-password checks, MFA enrollment/recovery controls.
5. Review all admin permissions and use database-level defenses such as row-level security where practical.
6. Add durable stock reservations, payment-provider webhook signature verification, replay protection, idempotency records, and appropriate PCI integration.
7. Add append-only, tamper-evident off-host audit exports and security alert routing; define human responders.
8. Implement backup encryption, independent key custody, off-site copies, retention, and recovery exercises with measured RPO/RTO.
9. Protect credentials with a managed secrets vault; enable rotation, least privilege and access reviews; keep signing/encryption keys independent.
10. Set up SAST, dependency scanning, SBOM, container scan, credential scan, release approvals, signed artifacts, and regular updates.
11. Independently test web/API security against OWASP ASVS 5.0 and API Security Top 10; validate access control with adversarial integration tests.
12. Commission architectural/engineering review of Nepal planning and price claims, and legal review of consent and privacy policies.
13. Configure centralized monitoring, threat detection, incident response, forensic evidence retention, and safe rollbacks.
14. Add schema migration tooling and backup-before-migration/rollback rehearsals.
15. Formalize data retention, access/export/deletion requests, regional profiling constraints and privacy notices.

## Practical incident response

- **Suspected admin account compromise:** disable or revoke its sessions, suspend user access, rotate affected credentials and TOTP secret, review privileged audit records; investigate rate/catalog tampering before re-approval.
- **Pricing sabotage:** suspend affected rates, restore previously approved versions, compare against independent supplier evidence; assess order impact.
- **DB compromise:** isolate network access, rotate DB and encryption credentials based on a documented key-rotation plan, preserve evidence and restore from verified clean backups if necessary.
- **Availability incident:** verify frontend and API health, PostgreSQL health, backup integrity and recent changes; roll back the last deployment if indicated.
- **Payment incident (future):** suspend checkout, reconcile provider records, and do not trust client-sent paid states.

## Debugging tips

| Symptom | Check |
|---|---|
| Products appear but prices say 'Request price' | Are any `material_rates` approved for the selected region? |
| Registration fails | `docker compose logs -f api` and PostgreSQL health |
| Admin login fails | Correct role, MFA provisioned with current 6-digit code, server time synchronized |
| Rate approval returns 403 | Approver must be Super Admin and **not the proposer** |
| Regional reports empty | Region names must match assigned scope and event/request region |
| HTTP 403 on account mutation | CSRF cookie/header, origin allowlist, active session |
| No behavioral analytics | Visitor selected Essential Only, browser/DB disconnected, or collection blocked |
| Browser blocks inline style/script | Expected under strict CSP; adjust code to use style classes and external scripts |
| Checkout submits without payment | Expected: development release only stores an order/quote request |

Official frameworks: https://owasp.org/www-project-application-security-verification-standard/ and https://owasp.org/API-Security/ and https://www.nist.gov/cyberframework .
