# Future cloud deployment — amarabati.com.np

DNS and ownership must be verified by the domain owner; this repository does not change DNS or perform deployment.

Proposed DNS names: `amarabati.com.np` (storefront), `admin.amarabati.com.np` (Super Admin), `regional.amarabati.com.np` (Regional Admin). Use company-owned infrastructure and certificates, and ensure admin surfaces receive tighter access/network policies than the public storefront.

When a cloud service is selected, use infrastructure as code and private network segments. PostgreSQL must have no public listener; treat the cloud application and database network as independently authenticated. Host identity/permissions should be independent from the app's Super Admin role. Keep key custody and DB backups under company ownership and test recovery before cutover.

Required launch inputs: cloud provider/region, DNS access, email/SMS provider, real business registration and contact details, price owners and suppliers, payment provider, Nepal geography coverage, delivery/tax rules, approved privacy terms and security incident contacts.

Before changing `APP_ENV=production`: provide 40+ char application signing secret, TOTP encryption key, `COOKIE_SECURE=true`, secure origins in `ALLOWED_ORIGINS`, an HTTPS termination layer with validated forwarded headers, managed secret and backup storage, and production-suitable rate-limiting/monitoring. The current Docker Compose settings are strictly for local development.
